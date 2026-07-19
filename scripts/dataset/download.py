"""Download the datasets declared in ``configs/datasets.yaml`` into ``datasets/raw/``.

Usage examples::

    python scripts/dataset/download.py --dry-run
    python scripts/dataset/download.py --datasets vnlp
    python scripts/dataset/download.py --all --force

Design notes
------------
**Nothing here is fatal by default.** A dataset that needs credentials the
machine does not have, a link that has expired, a checksum that does not match
-- each of these is reported clearly and the run moves on to the next dataset.
Phase 2 involves half a dozen sources of varying reliability, and a run that
aborts on the first bad one wastes the bandwidth already spent on the good ones.
The process exit code still reflects failures, so CI and ``run_pipeline.py``
notice.

**Resume is checksum-aware.** A file already present with a matching SHA-256 is
skipped. A file present when no checksum is declared is also skipped, but only
after a size sanity check, and the computed digest is printed so it can be
pasted back into the config -- that is how the config gets filled in over time.

**Credentials never appear in logs.** URLs may embed ``${VAR}`` placeholders
that expand from the environment; every log line runs through
:func:`_redact_url` first.
"""

from __future__ import annotations

import argparse
import hashlib
import logging
import os
import re
import shutil
import sys
import tarfile
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final, Iterable, Mapping, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (  # noqa: E402
    PROJECT_ROOT,
    DatasetPaths,
    add_common_arguments,
    bootstrap_project_path,
    configure_logging,
    resolve_dataset_paths,
    write_json,
)

bootstrap_project_path()

LOGGER = logging.getLogger("dataset.download")

VALID_SOURCE_TYPES: Final[frozenset[str]] = frozenset(
    {"roboflow", "kaggle", "github_release", "huggingface", "direct_url", "manual"}
)
VALID_ROLES: Final[frozenset[str]] = frozenset({"primary", "supplementary", "pretrain_only"})
_NAME_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[a-z0-9_]+$")
_ENV_PLACEHOLDER: Final[re.Pattern[str]] = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")
_CHUNK_SIZE: Final[int] = 1 << 20  # 1 MiB
_MIN_PLAUSIBLE_ARCHIVE_BYTES: Final[int] = 1024

#: Roboflow export formats tried in order when the catalogue's preferred format
#: is not offered for a given project version. All of them produce YOLO-style
#: ``images/`` + ``labels/`` trees, so downstream tooling does not care which
#: one was used -- but the choice is recorded in the export metadata sidecar.
ROBOFLOW_FORMAT_FALLBACKS: Final[tuple[str, ...]] = ("yolov11", "yolov9", "yolov8", "yolov5pytorch")

#: How long to keep polling Roboflow while it generates an export on demand.
_ROBOFLOW_POLL_ATTEMPTS: Final[int] = 30
_ROBOFLOW_POLL_SECONDS: Final[float] = 10.0

#: Sidecar written next to a Roboflow download recording which format actually
#: served the data. Never contains the API key.
ROBOFLOW_EXPORT_METADATA: Final[str] = "_roboflow_export.json"


class DownloadError(RuntimeError):
    """A dataset could not be fetched. Carries a message meant for a human."""


class ConfigError(ValueError):
    """The dataset catalogue is malformed. Always fatal -- the run cannot start."""


@dataclass(frozen=True, slots=True)
class DatasetSource:
    """One entry from the dataset catalogue.

    Attributes:
        name: Unique slug, also the directory name under ``datasets/raw/``.
        source_type: One of :data:`VALID_SOURCE_TYPES`.
        url: Download location or repository identifier. May contain
            ``${ENV_VAR}`` placeholders.
        label_format: Informational tag describing the annotation format.
        license_name: Licence, recorded so the thesis can cite it.
        license_url: Where the licence text lives.
        requires_credentials: Whether :attr:`credential_env` must be populated.
        credential_env: Environment variables that must be set to fetch this.
        archive_name: File name to save as. ``None`` derives it from the URL.
        sha256: Expected digest, or ``None`` when not yet known.
        extract: Unpack the archive after downloading.
        role: How the dataset is used -- see :data:`VALID_ROLES`.
        ocr_usable: ``False`` marks data that must never reach OCR training.
        expected_images: Rough image count, for cross-checking only.
        enabled: Whether a plain run includes this dataset.
        notes: Free-text guidance shown in ``--dry-run``.
    """

    name: str
    source_type: str
    url: str
    label_format: str = "unknown"
    license_name: str = "unknown"
    license_url: str = ""
    requires_credentials: bool = False
    credential_env: tuple[str, ...] = ()
    archive_name: str | None = None
    sha256: str | None = None
    extract: bool = True
    role: str = "supplementary"
    ocr_usable: bool = False
    expected_images: int | None = None
    enabled: bool = True
    notes: str = ""

    def target_dir(self, paths: DatasetPaths) -> Path:
        """Return this dataset's directory under ``datasets/raw/``.

        Args:
            paths: The resolved dataset layout.

        Returns:
            ``<datasets>/raw/<name>``.
        """
        return paths.raw / self.name

    def resolved_archive_name(self) -> str:
        """Return the file name to save the download as.

        Returns:
            :attr:`archive_name` when set, otherwise the last path segment of
            the URL with any query string stripped. Falls back to
            ``<name>.download`` when the URL has no usable segment (common for
            Roboflow export links).
        """
        if self.archive_name:
            return self.archive_name
        candidate = self.url.split("?", 1)[0].rstrip("/").rsplit("/", 1)[-1]
        return candidate if candidate and "." in candidate else f"{self.name}.download"


@dataclass(slots=True)
class DownloadOutcome:
    """What happened to one dataset during a run.

    Attributes:
        name: The dataset slug.
        status: ``"downloaded"``, ``"skipped"``, ``"cached"``, ``"planned"`` or
            ``"failed"``.
        message: Human-readable detail, including remediation steps on failure.
        destination: Where the data landed, when it landed anywhere.
        bytes_downloaded: Payload size, ``0`` when nothing was transferred.
        sha256: Digest of the fetched archive, when one was computed.
    """

    name: str
    status: str
    message: str = ""
    destination: Path | None = None
    bytes_downloaded: int = 0
    sha256: str | None = None

    @property
    def ok(self) -> bool:
        """Return ``True`` when this outcome is not a failure."""
        return self.status != "failed"

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable view for the run report."""
        return {
            "name": self.name,
            "status": self.status,
            "message": self.message,
            "destination": str(self.destination) if self.destination else None,
            "bytes_downloaded": self.bytes_downloaded,
            "sha256": self.sha256,
        }


# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------


def default_config_path() -> Path:
    """Return the catalogue path to use when ``--config`` is not given.

    Prefers ``<root>/configs/datasets.yaml`` if it exists, so a project-wide
    config can override the copy shipped next to these scripts.

    Returns:
        The first existing candidate, or the bundled path if neither exists (so
        the error message names the file the user most likely meant).
    """
    project_config = PROJECT_ROOT / "configs" / "datasets.yaml"
    bundled = Path(__file__).resolve().parent / "configs" / "datasets.yaml"
    return project_config if project_config.is_file() else bundled


def load_catalogue(config_path: Path) -> list[DatasetSource]:
    """Parse and validate the dataset catalogue.

    Args:
        config_path: Path to the YAML file.

    Returns:
        Every declared dataset, in file order, regardless of ``enabled``.

    Raises:
        ConfigError: If the file is missing, is not valid YAML, has the wrong
            shape, or declares a duplicate name or an unknown ``source_type``.
    """
    if not config_path.is_file():
        raise ConfigError(
            f"Dataset catalogue not found: {config_path}\n"
            "Create it, or point at another file with --config."
        )

    try:
        import yaml
    except ImportError as exc:  # pragma: no cover - dependency is declared
        raise ConfigError(
            "PyYAML is required to read the dataset catalogue. "
            "Install it with: pip install pyyaml"
        ) from exc

    try:
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigError(f"{config_path} is not valid YAML: {exc}") from exc
    except OSError as exc:
        raise ConfigError(f"Cannot read {config_path}: {exc}") from exc

    if not isinstance(raw, Mapping):
        raise ConfigError(f"{config_path}: top level must be a mapping, got {type(raw).__name__}")

    entries = raw.get("datasets")
    if not isinstance(entries, list) or not entries:
        raise ConfigError(f"{config_path}: key 'datasets' must be a non-empty list")

    sources: list[DatasetSource] = []
    seen: set[str] = set()
    for index, entry in enumerate(entries):
        source = _parse_entry(entry, index=index, config_path=config_path)
        if source.name in seen:
            raise ConfigError(f"{config_path}: duplicate dataset name {source.name!r}")
        seen.add(source.name)
        sources.append(source)

    LOGGER.debug("Loaded %d dataset definitions from %s", len(sources), config_path)
    return sources


def _parse_entry(entry: Any, *, index: int, config_path: Path) -> DatasetSource:
    """Turn one YAML mapping into a validated :class:`DatasetSource`.

    Args:
        entry: The raw mapping.
        index: Position in the list, used in error messages.
        config_path: File being parsed, used in error messages.

    Returns:
        The validated source.

    Raises:
        ConfigError: If a required key is missing or a value is invalid.
    """
    where = f"{config_path}: datasets[{index}]"
    if not isinstance(entry, Mapping):
        raise ConfigError(f"{where} must be a mapping, got {type(entry).__name__}")

    name = entry.get("name")
    if not isinstance(name, str) or not _NAME_PATTERN.match(name):
        raise ConfigError(
            f"{where}: 'name' must be a slug matching [a-z0-9_]+, got {name!r}"
        )

    source_type = entry.get("source_type")
    if source_type not in VALID_SOURCE_TYPES:
        raise ConfigError(
            f"{where} ({name}): 'source_type' must be one of "
            f"{sorted(VALID_SOURCE_TYPES)}, got {source_type!r}"
        )

    url = entry.get("url")
    if not isinstance(url, str) or not url.strip():
        raise ConfigError(f"{where} ({name}): 'url' must be a non-empty string")

    role = entry.get("role", "supplementary")
    if role not in VALID_ROLES:
        raise ConfigError(
            f"{where} ({name}): 'role' must be one of {sorted(VALID_ROLES)}, got {role!r}"
        )

    credential_env = entry.get("credential_env") or []
    if not isinstance(credential_env, list) or not all(
        isinstance(item, str) for item in credential_env
    ):
        raise ConfigError(f"{where} ({name}): 'credential_env' must be a list of strings")

    sha256 = entry.get("sha256")
    if sha256 is not None:
        if not isinstance(sha256, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", sha256):
            raise ConfigError(
                f"{where} ({name}): 'sha256' must be a 64-character hex digest or null"
            )
        sha256 = sha256.lower()

    expected_images = entry.get("expected_images")
    if expected_images is not None and not isinstance(expected_images, int):
        raise ConfigError(f"{where} ({name}): 'expected_images' must be an integer or null")

    archive_name = entry.get("archive_name")
    if archive_name is not None and not isinstance(archive_name, str):
        raise ConfigError(f"{where} ({name}): 'archive_name' must be a string or null")
    if archive_name and ("/" in archive_name or "\\" in archive_name or ".." in archive_name):
        raise ConfigError(
            f"{where} ({name}): 'archive_name' must be a bare file name, got {archive_name!r}"
        )

    return DatasetSource(
        name=name,
        source_type=source_type,
        url=url.strip(),
        label_format=str(entry.get("label_format", "unknown")),
        license_name=str(entry.get("license", "unknown")),
        license_url=str(entry.get("license_url", "")),
        requires_credentials=bool(entry.get("requires_credentials", False)),
        credential_env=tuple(credential_env),
        archive_name=archive_name,
        sha256=sha256,
        extract=bool(entry.get("extract", True)),
        role=role,
        ocr_usable=bool(entry.get("ocr_usable", False)),
        expected_images=expected_images,
        enabled=bool(entry.get("enabled", True)),
        notes=str(entry.get("notes", "")).strip(),
    )


# --------------------------------------------------------------------------
# Credentials and URLs
# --------------------------------------------------------------------------


def load_dotenv(path: Path | None = None) -> list[str]:
    """Load ``KEY=VALUE`` pairs from the project ``.env`` into the environment.

    Existing environment variables always win, so an operator can override a
    committed default from the shell. Values are never logged: only the names
    of the variables that were set are returned.

    Args:
        path: The file to read. Defaults to ``<project root>/.env``.

    Returns:
        Names of the variables this call introduced, sorted.
    """
    env_path = path or (PROJECT_ROOT / ".env")
    if not env_path.is_file():
        return []

    introduced: list[str] = []
    try:
        text = env_path.read_text(encoding="utf-8")
    except OSError as exc:
        LOGGER.warning("Could not read %s: %s", env_path, exc)
        return []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.lower().startswith("export "):
            line = line[len("export ") :].lstrip()
        name, _, value = line.partition("=")
        name = name.strip()
        value = value.strip().strip("'\"")
        if not name or not value or os.environ.get(name):
            continue
        os.environ[name] = value
        introduced.append(name)

    if introduced:
        LOGGER.debug("Loaded %d variable(s) from %s", len(introduced), env_path)
    return sorted(introduced)


def missing_credentials(source: DatasetSource) -> list[str]:
    """Return the environment variables this dataset needs but does not have.

    Args:
        source: The dataset definition.

    Returns:
        Names of unset or empty variables, empty when everything is present.
    """
    required = set(source.credential_env)
    required.update(_ENV_PLACEHOLDER.findall(source.url))
    return sorted(name for name in required if not os.environ.get(name))


def credential_help(source: DatasetSource, missing: Sequence[str]) -> str:
    """Build actionable instructions for supplying missing credentials.

    Args:
        source: The dataset that could not be fetched.
        missing: The variables that are absent.

    Returns:
        A multi-line message naming the variables and the concrete steps for
        this particular source type.
    """
    lines = [
        f"Dataset '{source.name}' needs credentials that are not set: {', '.join(missing)}.",
        "",
        "Set them for the current PowerShell session with:",
    ]
    lines.extend(f'    $env:{name} = "<your value>"' for name in missing)
    lines.append("")

    if source.source_type == "kaggle":
        lines += [
            "Kaggle: sign in at https://www.kaggle.com, open Settings -> API ->",
            "'Create New Token'. That downloads kaggle.json. Either place it at",
            r"    %USERPROFILE%\.kaggle\kaggle.json",
            "or copy its two values into KAGGLE_USERNAME and KAGGLE_KEY.",
            "You must also accept the dataset's rules on its Kaggle page first,",
            "otherwise the API returns 403 even with valid credentials.",
        ]
    elif source.source_type == "roboflow":
        lines += [
            "Roboflow: sign in at https://roboflow.com, open the project, choose",
            "Download Dataset -> Format: YOLOv11 -> 'show download code'. Copy the",
            "API key into ROBOFLOW_API_KEY and paste the export URL into",
            "the catalogue's 'url' field. Export links expire, so re-copy the URL",
            "if the download returns 401 or 404.",
        ]
    elif source.source_type == "huggingface":
        lines += [
            "Hugging Face: create a read token at",
            "https://huggingface.co/settings/tokens and set HF_TOKEN.",
            "For a gated dataset you must also accept its terms on the dataset page.",
        ]

    lines += ["", f"Then re-run:  python {Path(__file__).name} --datasets {source.name}"]
    return "\n".join(lines)


def expand_url(url: str) -> str:
    """Substitute ``${VAR}`` placeholders in a URL from the environment.

    Args:
        url: The raw URL from the catalogue.

    Returns:
        The URL with every placeholder replaced.

    Raises:
        DownloadError: If a referenced variable is not set. Callers check
            :func:`missing_credentials` first, so reaching this is a bug in the
            caller rather than a user error -- but failing loudly beats sending
            a literal ``${...}`` to a server.
    """

    def _replace(match: re.Match[str]) -> str:
        value = os.environ.get(match.group(1))
        if not value:
            raise DownloadError(f"Environment variable {match.group(1)} is not set")
        return value

    return _ENV_PLACEHOLDER.sub(_replace, url)


def _redact_url(url: str) -> str:
    """Mask secrets in a URL so it is safe to log.

    Args:
        url: A URL that may carry an API key in its query string.

    Returns:
        The URL with the values of key-like query parameters replaced by
        ``***``.
    """
    return re.sub(
        r"([?&](?:key|api_key|apikey|token|access_token)=)[^&]*",
        r"\1***",
        url,
        flags=re.IGNORECASE,
    )


# --------------------------------------------------------------------------
# Checksums
# --------------------------------------------------------------------------


def compute_sha256(path: Path, *, show_progress: bool = False) -> str:
    """Compute a file's SHA-256 digest, reading it in chunks.

    Args:
        path: File to hash.
        show_progress: Show a ``tqdm`` bar for large files.

    Returns:
        The lowercase hex digest.

    Raises:
        OSError: If the file cannot be read.
    """
    digest = hashlib.sha256()
    total = path.stat().st_size
    bar = None
    if show_progress and total > 32 * 1024 * 1024:
        try:
            from tqdm import tqdm

            bar = tqdm(total=total, unit="B", unit_scale=True, desc=f"hash {path.name}")
        except ImportError:
            bar = None

    try:
        with path.open("rb") as handle:
            while chunk := handle.read(_CHUNK_SIZE):
                digest.update(chunk)
                if bar is not None:
                    bar.update(len(chunk))
    finally:
        if bar is not None:
            bar.close()
    return digest.hexdigest()


def verify_checksum(path: Path, expected: str | None) -> tuple[bool, str]:
    """Check a file against an expected digest.

    Args:
        path: File to verify.
        expected: Expected lowercase hex digest, or ``None`` to skip
            verification.

    Returns:
        ``(matches, actual_digest)``. When ``expected`` is ``None`` the first
        element is ``True`` and the digest is still computed and returned, so
        the caller can print it for the user to record.

    Raises:
        OSError: If the file cannot be read.
    """
    actual = compute_sha256(path, show_progress=True)
    if expected is None:
        return True, actual
    return actual == expected.lower(), actual


# --------------------------------------------------------------------------
# Transfer
# --------------------------------------------------------------------------


def download_file(url: str, destination: Path, *, timeout: float = 60.0) -> int:
    """Stream a URL to disk, writing through a temporary file.

    The download lands on ``<destination>.part`` and is only renamed into place
    once the transfer completes. A run interrupted halfway therefore cannot
    leave a truncated file that a later run mistakes for a finished download --
    the single most annoying failure mode of a naive resume implementation.

    Args:
        url: Fully expanded URL.
        destination: Final file path. Parent directories are created.
        timeout: Per-request timeout in seconds.

    Returns:
        Number of bytes written.

    Raises:
        DownloadError: On any network or HTTP failure, or if the server returns
            an HTML error page instead of the expected payload.
    """
    try:
        import requests
    except ImportError as exc:  # pragma: no cover - dependency is declared
        raise DownloadError(
            "The 'requests' package is required to download files. "
            "Install it with: pip install requests"
        ) from exc

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".part")

    LOGGER.info("Downloading %s -> %s", _redact_url(url), destination)
    try:
        with requests.get(url, stream=True, timeout=timeout, allow_redirects=True) as response:
            if response.status_code >= 400:
                raise DownloadError(
                    f"Server returned HTTP {response.status_code} for "
                    f"{_redact_url(url)}. If this is 401/403 the credentials or "
                    "dataset permissions are wrong; if 404 the export link has "
                    "most likely expired and must be regenerated."
                )

            content_type = response.headers.get("Content-Type", "")
            if content_type.startswith("text/html"):
                raise DownloadError(
                    f"{_redact_url(url)} returned an HTML page rather than a file. "
                    "This usually means a login page or an expired export link."
                )

            total = int(response.headers.get("Content-Length") or 0)
            bar = _transfer_bar(total, destination.name)
            written = 0
            try:
                with temporary.open("wb") as handle:
                    for chunk in response.iter_content(chunk_size=_CHUNK_SIZE):
                        if not chunk:
                            continue
                        handle.write(chunk)
                        written += len(chunk)
                        if bar is not None:
                            bar.update(len(chunk))
            finally:
                if bar is not None:
                    bar.close()
    except DownloadError:
        temporary.unlink(missing_ok=True)
        raise
    except Exception as exc:  # noqa: BLE001 - requests raises a wide family
        temporary.unlink(missing_ok=True)
        raise DownloadError(f"Transfer failed for {_redact_url(url)}: {exc}") from exc

    if written < _MIN_PLAUSIBLE_ARCHIVE_BYTES:
        temporary.unlink(missing_ok=True)
        raise DownloadError(
            f"Downloaded only {written} bytes from {_redact_url(url)}, which cannot "
            "be a dataset archive. The link is probably broken."
        )

    temporary.replace(destination)
    LOGGER.info("Saved %.1f MiB to %s", written / (1 << 20), destination)
    return written


def _transfer_bar(total: int, name: str) -> Any | None:
    """Create a ``tqdm`` byte progress bar, or ``None`` if unavailable.

    Args:
        total: Expected byte count, ``0`` when the server did not say.
        name: Label for the bar.

    Returns:
        A ``tqdm`` instance or ``None``.
    """
    try:
        from tqdm import tqdm
    except ImportError:
        return None
    return tqdm(total=total or None, unit="B", unit_scale=True, desc=name)


def extract_archive(archive: Path, destination: Path) -> None:
    """Unpack a zip or tar archive, refusing paths that escape the destination.

    Archive members are checked against the destination before extraction. A
    crafted archive containing ``../../etc/passwd`` or an absolute path would
    otherwise write outside the dataset tree; these files come from third-party
    hosting, so the check is not paranoia.

    Args:
        archive: The ``.zip``, ``.tar``, ``.tar.gz``, ``.tgz``, ``.tar.xz`` or
            ``.tar.bz2`` file.
        destination: Directory to unpack into. Created if absent.

    Raises:
        DownloadError: If the format is unsupported, the archive is corrupt, or
            a member would land outside ``destination``.
    """
    destination.mkdir(parents=True, exist_ok=True)
    resolved_root = destination.resolve()

    def _guard(member_name: str) -> None:
        target = (destination / member_name).resolve()
        if resolved_root != target and resolved_root not in target.parents:
            raise DownloadError(
                f"Archive {archive.name} contains an unsafe path {member_name!r} "
                "that would extract outside the destination directory. Refusing."
            )

    LOGGER.info("Extracting %s -> %s", archive.name, destination)
    try:
        if zipfile.is_zipfile(archive):
            with zipfile.ZipFile(archive) as bundle:
                for member in bundle.namelist():
                    _guard(member)
                bundle.extractall(destination)
        elif tarfile.is_tarfile(archive):
            with tarfile.open(archive) as bundle:
                for member in bundle.getmembers():
                    if member.islnk() or member.issym():
                        raise DownloadError(
                            f"Archive {archive.name} contains a link member "
                            f"{member.name!r}; refusing to extract."
                        )
                    _guard(member.name)
                bundle.extractall(destination)
        else:
            raise DownloadError(
                f"{archive.name} is neither a zip nor a tar archive. Set "
                "'extract: false' in the catalogue if it is a plain file."
            )
    except DownloadError:
        raise
    except (zipfile.BadZipFile, tarfile.TarError, EOFError) as exc:
        raise DownloadError(
            f"{archive.name} is corrupt and cannot be extracted ({exc}). "
            "Delete it and download again with --force."
        ) from exc


# --------------------------------------------------------------------------
# Per-source handlers
# --------------------------------------------------------------------------


def fetch_kaggle(source: DatasetSource, target_dir: Path) -> int:
    """Fetch a Kaggle dataset through the official client.

    Args:
        source: Catalogue entry whose ``url`` is a ``owner/dataset`` slug.
        target_dir: Where to unpack.

    Returns:
        Total bytes on disk after the download.

    Raises:
        DownloadError: If the ``kaggle`` package is missing or the API refuses.
    """
    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
    except ImportError as exc:
        raise DownloadError(
            "The 'kaggle' package is not installed, so Kaggle datasets cannot be\n"
            "fetched automatically. Either install it:\n"
            "    pip install kaggle\n"
            "or download the archive by hand from\n"
            f"    https://www.kaggle.com/datasets/{source.url}\n"
            f"and unpack it into {target_dir}"
        ) from exc
    except OSError as exc:
        raise DownloadError(
            f"The kaggle client could not start: {exc}\n"
            "This normally means kaggle.json is missing or unreadable."
        ) from exc

    try:
        api = KaggleApi()
        api.authenticate()
        target_dir.mkdir(parents=True, exist_ok=True)
        api.dataset_download_files(source.url, path=str(target_dir), unzip=source.extract)
    except Exception as exc:  # noqa: BLE001 - the client raises many types
        raise DownloadError(
            f"Kaggle download of {source.url!r} failed: {exc}\n"
            "Check that the slug is correct and that you have accepted the "
            "dataset rules on its Kaggle page."
        ) from exc

    return _directory_size(target_dir)


def fetch_huggingface(source: DatasetSource, target_dir: Path) -> int:
    """Fetch a Hugging Face dataset repository snapshot.

    Args:
        source: Catalogue entry whose ``url`` is a ``owner/name`` repo id.
        target_dir: Local directory to mirror the repo into.

    Returns:
        Total bytes on disk after the download.

    Raises:
        DownloadError: If ``huggingface_hub`` is missing or the fetch fails.
    """
    try:
        from huggingface_hub import snapshot_download
    except ImportError as exc:
        raise DownloadError(
            "The 'huggingface_hub' package is not installed, so this dataset\n"
            "cannot be fetched automatically. Either install it:\n"
            "    pip install huggingface_hub\n"
            "or download it by hand:\n"
            f"    huggingface-cli download {source.url} --repo-type dataset "
            f"--local-dir {target_dir}"
        ) from exc

    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        snapshot_download(
            repo_id=source.url,
            repo_type="dataset",
            local_dir=str(target_dir),
            token=os.environ.get("HF_TOKEN") or None,
        )
    except Exception as exc:  # noqa: BLE001 - hub raises many types
        raise DownloadError(
            f"Hugging Face download of {source.url!r} failed: {exc}\n"
            "If the dataset is gated, accept its terms on the dataset page and "
            "set HF_TOKEN to a read token."
        ) from exc

    return _directory_size(target_dir)


def _swap_roboflow_format(api_url: str, export_format: str) -> str:
    """Return ``api_url`` with its trailing export-format segment replaced.

    Args:
        api_url: A ``https://api.roboflow.com/{ws}/{proj}/{ver}/{format}?...`` URL.
        export_format: The format to substitute in.

    Returns:
        The rewritten URL, query string preserved.
    """
    base, sep, query = api_url.partition("?")
    head, _, _tail = base.rstrip("/").rpartition("/")
    return f"{head}/{export_format}{sep}{query}"


def _roboflow_api_format(api_url: str) -> str:
    """Return the export format named in a Roboflow API URL.

    Args:
        api_url: The catalogue URL for a Roboflow dataset version.

    Returns:
        The last path segment before the query string, e.g. ``"yolov11"``.
    """
    return api_url.partition("?")[0].rstrip("/").rpartition("/")[2]


def resolve_roboflow_export(
    api_url: str, *, timeout: float, formats: Sequence[str] | None = None
) -> tuple[str, str, dict[str, Any]]:
    """Ask Roboflow for a signed download link (step 1 of the two-step fetch).

    Roboflow does not serve dataset archives from a stable URL. The documented
    flow is to ``GET`` the version endpoint, which either returns an
    ``export.link`` (a short-lived signed URL) or a ``progress`` value while the
    export is still being generated. This function polls until the link appears
    and falls back through :data:`ROBOFLOW_FORMAT_FALLBACKS` when a project does
    not offer the requested format.

    Args:
        api_url: Fully expanded ``https://api.roboflow.com/...`` URL, key included.
        timeout: Per-request network timeout in seconds.
        formats: Export formats to try, most preferred first. Defaults to the
            format named in ``api_url`` followed by the standard fallbacks.

    Returns:
        A tuple of ``(signed_link, format_used, version_info)`` where
        ``version_info`` is the ``version`` object Roboflow returned (image
        counts, splits) with no credential material in it.

    Raises:
        DownloadError: If no format yielded a link, or the API refused the key.
    """
    import time

    import requests

    preferred = _roboflow_api_format(api_url)
    candidates: list[str] = []
    for candidate in [*(formats or ()), preferred, *ROBOFLOW_FORMAT_FALLBACKS]:
        if candidate and candidate not in candidates:
            candidates.append(candidate)

    problems: list[str] = []
    for export_format in candidates:
        url = _swap_roboflow_format(api_url, export_format)
        LOGGER.info("Requesting Roboflow export: %s", _redact_url(url))
        for attempt in range(1, _ROBOFLOW_POLL_ATTEMPTS + 1):
            try:
                response = requests.get(url, timeout=timeout)
            except Exception as exc:  # noqa: BLE001 - requests raises a wide family
                problems.append(f"{export_format}: request failed ({exc})")
                break

            if response.status_code in (401, 403):
                raise DownloadError(
                    f"Roboflow rejected the API key for {_redact_url(url)} "
                    f"(HTTP {response.status_code}). Check ROBOFLOW_API_KEY."
                )
            if response.status_code == 404:
                problems.append(f"{export_format}: HTTP 404 (format or version not available)")
                break
            if response.status_code >= 400:
                problems.append(f"{export_format}: HTTP {response.status_code}")
                break

            try:
                payload = response.json()
            except ValueError:
                problems.append(f"{export_format}: response was not JSON")
                break

            link = (payload.get("export") or {}).get("link")
            if link:
                version_info = payload.get("version") or {}
                LOGGER.info(
                    "Roboflow export ready (format=%s, %s images, ~%.1f MiB)",
                    export_format,
                    version_info.get("images", "?"),
                    float((payload.get("export") or {}).get("size") or 0.0),
                )
                return str(link), export_format, dict(version_info)

            progress = payload.get("progress")
            if progress is None:
                offered = (payload.get("version") or {}).get("exports")
                problems.append(f"{export_format}: no export link (available: {offered})")
                break

            LOGGER.info(
                "Roboflow is still generating the %s export (progress %.0f%%, "
                "attempt %d/%d); waiting %.0fs",
                export_format,
                float(progress) * 100.0,
                attempt,
                _ROBOFLOW_POLL_ATTEMPTS,
                _ROBOFLOW_POLL_SECONDS,
            )
            time.sleep(_ROBOFLOW_POLL_SECONDS)
        else:
            problems.append(f"{export_format}: still generating after polling timed out")

    raise DownloadError(
        "Roboflow did not return a download link for "
        f"{_redact_url(api_url)}.\nTried: " + "; ".join(problems)
    )


def _process_roboflow_source(
    source: DatasetSource, target_dir: Path, *, force: bool, timeout: float
) -> DownloadOutcome:
    """Fetch a Roboflow dataset version using the two-step export flow.

    Step 1 resolves a signed link via :func:`resolve_roboflow_export`; step 2
    downloads that link like any other archive. A cached archive short-circuits
    both steps, so re-runs cost no API calls.

    Args:
        source: The catalogue entry, whose ``url`` points at ``api.roboflow.com``.
        target_dir: Directory for the archive and its extracted contents.
        force: Ignore any cached archive.
        timeout: Per-request timeout in seconds.

    Returns:
        The outcome.

    Raises:
        DownloadError: On resolution, transfer or extraction failure.
    """
    archive_path = target_dir / source.resolved_archive_name()

    if archive_path.is_file() and not force:
        matches, actual = verify_checksum(archive_path, source.sha256)
        if matches:
            if source.extract:
                extract_archive(archive_path, target_dir)
            return DownloadOutcome(
                name=source.name,
                status="cached",
                message=f"Archive already present and valid: {archive_path}",
                destination=target_dir,
                sha256=actual,
                bytes_downloaded=archive_path.stat().st_size,
            )
        LOGGER.warning(
            "Cached archive for '%s' does not match the declared digest; re-downloading.",
            source.name,
        )

    api_url = expand_url(source.url)
    link, export_format, version_info = resolve_roboflow_export(api_url, timeout=timeout)

    written = download_file(link, archive_path, timeout=timeout)

    matches, actual = verify_checksum(archive_path, source.sha256)
    if not matches:
        archive_path.unlink(missing_ok=True)
        raise DownloadError(
            f"Checksum mismatch for '{source.name}'.\n"
            f"  expected: {source.sha256}\n  actual:   {actual}\n"
            "The bad file has been deleted; update 'sha256' if the source changed."
        )

    write_json(
        target_dir / ROBOFLOW_EXPORT_METADATA,
        {
            "dataset": source.name,
            "api_url": _redact_url(source.url),
            "format_requested": _roboflow_api_format(source.url),
            "format_used": export_format,
            "archive": archive_path.name,
            "archive_bytes": written,
            "sha256": actual,
            "version_images": version_info.get("images"),
            "version_splits": version_info.get("splits"),
        },
    )

    if source.extract:
        extract_archive(archive_path, target_dir)

    return DownloadOutcome(
        name=source.name,
        status="downloaded",
        message=f"Roboflow export fetched using format '{export_format}'",
        destination=target_dir,
        bytes_downloaded=written,
        sha256=actual,
    )


def _directory_size(directory: Path) -> int:
    """Return the total size in bytes of every file under a directory.

    Args:
        directory: Directory to measure.

    Returns:
        Total bytes; ``0`` when the directory does not exist.
    """
    if not directory.is_dir():
        return 0
    return sum(path.stat().st_size for path in directory.rglob("*") if path.is_file())


# --------------------------------------------------------------------------
# Orchestration
# --------------------------------------------------------------------------


def process_source(
    source: DatasetSource, paths: DatasetPaths, *, force: bool = False, timeout: float = 60.0
) -> DownloadOutcome:
    """Fetch a single dataset, returning an outcome instead of raising.

    Args:
        source: The dataset to fetch.
        paths: Resolved dataset layout.
        force: Re-download even when a valid cached copy exists.
        timeout: Per-request network timeout in seconds.

    Returns:
        The outcome. Failures are captured as ``status="failed"`` with a
        remediation message; nothing propagates out.
    """
    target_dir = source.target_dir(paths)

    missing = missing_credentials(source)
    if missing:
        return DownloadOutcome(
            name=source.name,
            status="skipped",
            message=credential_help(source, missing),
            destination=target_dir,
        )

    if source.source_type == "manual":
        return DownloadOutcome(
            name=source.name,
            status="skipped",
            message=(
                f"'{source.name}' is marked source_type: manual and must be fetched by hand.\n"
                f"Obtain it from {source.url}\n"
                f"and unpack it into {target_dir}\n"
                + (f"Notes: {source.notes}" if source.notes else "")
            ),
            destination=target_dir,
        )

    try:
        if source.source_type == "kaggle":
            written = fetch_kaggle(source, target_dir)
            return DownloadOutcome(
                name=source.name,
                status="downloaded",
                message=f"Kaggle dataset {source.url} fetched",
                destination=target_dir,
                bytes_downloaded=written,
            )

        if source.source_type == "huggingface":
            if target_dir.is_dir() and any(target_dir.iterdir()) and not force:
                return DownloadOutcome(
                    name=source.name,
                    status="cached",
                    message=f"{target_dir} is already populated; use --force to refetch",
                    destination=target_dir,
                    bytes_downloaded=_directory_size(target_dir),
                )
            written = fetch_huggingface(source, target_dir)
            return DownloadOutcome(
                name=source.name,
                status="downloaded",
                message=f"Hugging Face dataset {source.url} fetched",
                destination=target_dir,
                bytes_downloaded=written,
            )

        if source.source_type == "roboflow":
            return _process_roboflow_source(source, target_dir, force=force, timeout=timeout)

        # github_release / direct_url both reduce to a plain HTTP GET.
        return _process_http_source(source, target_dir, force=force, timeout=timeout)

    except DownloadError as exc:
        return DownloadOutcome(
            name=source.name, status="failed", message=str(exc), destination=target_dir
        )
    except OSError as exc:
        return DownloadOutcome(
            name=source.name,
            status="failed",
            message=f"Filesystem error while handling '{source.name}': {exc}",
            destination=target_dir,
        )


def _process_http_source(
    source: DatasetSource, target_dir: Path, *, force: bool, timeout: float
) -> DownloadOutcome:
    """Handle the download-an-archive-over-HTTP case, including resume.

    Args:
        source: The dataset to fetch.
        target_dir: Directory for the archive and its extracted contents.
        force: Ignore any cached archive.
        timeout: Per-request timeout in seconds.

    Returns:
        The outcome.

    Raises:
        DownloadError: On transfer, checksum or extraction failure.
    """
    archive_path = target_dir / source.resolved_archive_name()

    if archive_path.is_file() and not force:
        matches, actual = verify_checksum(archive_path, source.sha256)
        if matches:
            if source.sha256 is None:
                LOGGER.warning(
                    "'%s' has no declared sha256. The cached archive hashes to %s -- "
                    "paste that into the catalogue to enable integrity checking.",
                    source.name,
                    actual,
                )
            if source.extract:
                extract_archive(archive_path, target_dir)
            return DownloadOutcome(
                name=source.name,
                status="cached",
                message=f"Archive already present and valid: {archive_path}",
                destination=target_dir,
                sha256=actual,
            )
        LOGGER.warning(
            "Cached archive for '%s' has digest %s but the catalogue expects %s. "
            "Re-downloading.",
            source.name,
            actual,
            source.sha256,
        )

    url = expand_url(source.url)
    written = download_file(url, archive_path, timeout=timeout)

    matches, actual = verify_checksum(archive_path, source.sha256)
    if not matches:
        archive_path.unlink(missing_ok=True)
        raise DownloadError(
            f"Checksum mismatch for '{source.name}'.\n"
            f"  expected: {source.sha256}\n"
            f"  actual:   {actual}\n"
            "The download is corrupt or the remote file changed. The bad file has "
            "been deleted; if the source legitimately changed, update 'sha256' in "
            "the catalogue."
        )
    if source.sha256 is None:
        LOGGER.warning(
            "'%s' has no declared sha256. Record this digest in the catalogue: %s",
            source.name,
            actual,
        )

    if source.extract:
        extract_archive(archive_path, target_dir)

    return DownloadOutcome(
        name=source.name,
        status="downloaded",
        message=f"Fetched and verified {archive_path.name}",
        destination=target_dir,
        bytes_downloaded=written,
        sha256=actual,
    )


def select_sources(
    catalogue: Sequence[DatasetSource], *, names: Sequence[str] | None, include_all: bool
) -> list[DatasetSource]:
    """Choose which catalogue entries this run should touch.

    Args:
        catalogue: Every declared dataset.
        names: Explicit ``--datasets`` selection. Selecting a dataset by name
            overrides its ``enabled: false`` flag, which is how the disabled
            entries in the shipped config get used.
        include_all: ``--all``, meaning every entry regardless of ``enabled``.

    Returns:
        The datasets to process, in catalogue order.

    Raises:
        ConfigError: If a requested name is not in the catalogue.
    """
    if names:
        by_name = {source.name: source for source in catalogue}
        unknown = [name for name in names if name not in by_name]
        if unknown:
            raise ConfigError(
                f"Unknown dataset name(s): {', '.join(unknown)}. "
                f"Available: {', '.join(sorted(by_name))}"
            )
        return [source for source in catalogue if source.name in set(names)]

    if include_all:
        return list(catalogue)
    return [source for source in catalogue if source.enabled]


def render_plan(sources: Sequence[DatasetSource], paths: DatasetPaths) -> str:
    """Render the ``--dry-run`` plan as readable text.

    Args:
        sources: The datasets that would be processed.
        paths: Resolved dataset layout, so destinations can be shown.

    Returns:
        A multi-line report.
    """
    lines = [
        "=" * 78,
        f"DRY RUN - {len(sources)} dataset(s) would be processed",
        f"Destination root: {paths.raw}",
        "=" * 78,
    ]

    for source in sources:
        missing = missing_credentials(source)
        lines += [
            "",
            f"[{source.name}]",
            f"  source type   : {source.source_type}",
            f"  url           : {_redact_url(source.url)}",
            f"  destination   : {source.target_dir(paths)}",
            f"  label format  : {source.label_format}",
            f"  licence       : {source.license_name}"
            + (f"  ({source.license_url})" if source.license_url else ""),
            f"  role          : {source.role}",
            f"  OCR usable    : {'yes' if source.ocr_usable else 'NO'}",
            f"  checksum      : {source.sha256 or 'not declared'}",
            f"  extract       : {'yes' if source.extract else 'no'}",
        ]
        if source.expected_images is not None:
            lines.append(f"  approx images : {source.expected_images:,}")
        if missing:
            lines.append(f"  STATUS        : WOULD SKIP - missing env: {', '.join(missing)}")
        elif source.source_type == "manual":
            lines.append("  STATUS        : WOULD SKIP - manual download required")
        else:
            lines.append("  STATUS        : would download")
        if source.notes:
            lines.append(f"  notes         : {source.notes}")

    total = sum(source.expected_images or 0 for source in sources)
    lines += [
        "",
        "-" * 78,
        f"Sum of 'expected_images' across the selection: {total:,}",
        "WARNING: that sum is NOT the real image count. The public Vietnamese",
        "plate datasets overlap heavily; only deduplicate.py can tell you how",
        "many distinct images you actually have.",
        "-" * 78,
    ]
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    """Construct the command-line parser.

    Returns:
        The configured parser.
    """
    parser = argparse.ArgumentParser(
        prog="download.py",
        description=(
            "Download the Vietnamese license plate datasets declared in the "
            "catalogue into datasets/raw/<name>/."
        ),
        epilog=(
            "Examples:\n"
            "  python download.py --dry-run\n"
            "  python download.py --datasets vnlp\n"
            "  python download.py --all --force\n\n"
            "Missing credentials never abort the run: the dataset is skipped with\n"
            "instructions and the exit code reflects it."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        metavar="FILE",
        help=(
            "Dataset catalogue YAML. Defaults to <root>/configs/datasets.yaml if "
            "present, otherwise scripts/dataset/configs/datasets.yaml."
        ),
    )
    parser.add_argument(
        "--datasets",
        nargs="+",
        metavar="NAME",
        help=(
            "Only process these datasets, by name. Naming a dataset overrides its "
            "'enabled: false' flag in the catalogue."
        ),
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Process every catalogue entry, including those marked disabled.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be downloaded and exit without touching the network.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download even when a valid cached archive is already present.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=60.0,
        metavar="SECONDS",
        help="Per-request network timeout (default: %(default)s).",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        metavar="FILE",
        help="Write a JSON run report here (default: <datasets>/reports/download_report.json).",
    )
    return add_common_arguments(parser)


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point.

    Args:
        argv: Argument list, defaulting to ``sys.argv[1:]``.

    Returns:
        ``0`` if every selected dataset was downloaded, cached or deliberately
        skipped; ``1`` if any dataset failed or the configuration is invalid.
    """
    args = build_parser().parse_args(argv)
    configure_logging(args.log_level)

    loaded = load_dotenv()
    if loaded:
        LOGGER.info("Loaded credentials from .env: %s", ", ".join(loaded))

    paths = resolve_dataset_paths(args.datasets_dir)

    try:
        config_path = args.config or default_config_path()
        catalogue = load_catalogue(config_path)
        sources = select_sources(catalogue, names=args.datasets, include_all=args.all)
    except ConfigError as exc:
        LOGGER.error("%s", exc)
        return 1

    if not sources:
        LOGGER.warning(
            "No datasets selected. Every entry in %s is disabled; use --all or "
            "--datasets NAME.",
            config_path,
        )
        return 0

    LOGGER.info("Catalogue: %s (%d entries selected)", config_path, len(sources))

    if args.dry_run:
        print(render_plan(sources, paths))
        return 0

    paths.ensure()
    outcomes: list[DownloadOutcome] = []
    for source in sources:
        LOGGER.info("--- %s (%s) ---", source.name, source.source_type)
        outcome = process_source(source, paths, force=args.force, timeout=args.timeout)
        outcomes.append(outcome)
        if outcome.status == "failed":
            LOGGER.error("FAILED %s\n%s", source.name, outcome.message)
        elif outcome.status == "skipped":
            LOGGER.warning("SKIPPED %s\n%s", source.name, outcome.message)
        else:
            LOGGER.info("%s: %s", outcome.status.upper(), outcome.message)

    report_path = args.report or (paths.reports / "download_report.json")
    write_json(
        report_path,
        {
            "config": str(config_path),
            "datasets_root": str(paths.root),
            "outcomes": [outcome.as_dict() for outcome in outcomes],
        },
    )

    failed = [outcome.name for outcome in outcomes if outcome.status == "failed"]
    skipped = [outcome.name for outcome in outcomes if outcome.status == "skipped"]
    LOGGER.info(
        "Done. %d ok, %d skipped, %d failed. Report: %s",
        len(outcomes) - len(failed) - len(skipped),
        len(skipped),
        len(failed),
        report_path,
    )
    if failed:
        LOGGER.error("Failed datasets: %s", ", ".join(failed))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
