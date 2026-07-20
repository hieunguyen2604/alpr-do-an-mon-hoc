"""Automated enforcement of the architectural constraints (NFR-M1, NFR-M4).

The architecture documents promise that the ``ai`` package is framework-free:
importing it must not drag in the web framework or its schema library, so the
inference stack stays usable from a notebook, a benchmark script or a Colab
runtime with no server installed.

A promise in a document decays. These tests make it executable.

Why a subprocess
----------------
The obvious check -- ``import ai.inference`` then look at ``sys.modules`` -- is
worthless inside this suite, because the integration tests import ``backend``
and put the web framework into ``sys.modules`` before this file ever runs. The
import must therefore be observed in a **fresh interpreter** that has imported
nothing else. That is what the subprocess is for, and why the check cannot be
simplified away.

A note on the source scan
-------------------------
The grep below deliberately matches lowercase *import statements* only. The
documentation inside ``ai/`` refers to the two libraries by their capitalised
product names precisely so that prose explaining the constraint is not mistaken
for a violation of it.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
AI_PACKAGE = PROJECT_ROOT / "ai"

FORBIDDEN_IN_AI = ("fastapi", "pydantic", "pydantic_settings", "starlette")
"""Modules **no** file anywhere under ``ai/`` may import.

This is NFR-M1 exactly as written: the web framework and its schema library.
The ASGI toolkit is included because it arrives transitively with the framework,
so importing it is the same mistake one step removed.
"""

FORBIDDEN_IN_INFERENCE = FORBIDDEN_IN_AI + ("sqlalchemy", "backend")
"""Additionally forbidden inside ``ai/inference/`` -- the inference tier proper.

The ORM and the service package are barred here rather than package-wide, and
the distinction is deliberate rather than a concession:

``ai/inference/`` is the tier the architecture makes a promise about. It has to
run inside a notebook, a benchmark and a Colab runtime with no server and no
database present, so a dependency on either would break the promise outright.

``ai/evaluation/`` is a **measurement harness**, not a runtime tier. Its stress
test exists to measure NFR-P6 -- history queries over 10 000 records -- which it
cannot do without the schema whose performance is the subject of the
measurement. Its imports are function-local, so nothing is pulled in merely by
importing the module. Forbidding them would not make the architecture cleaner;
it would only make the requirement unmeasurable.
"""

INFERENCE_PACKAGE = AI_PACKAGE / "inference"

_IMPORT_PATTERN = re.compile(
    r"^[ \t]*(?:from[ \t]+(?P<from>[\w.]+)|import[ \t]+(?P<import>[\w.]+))",
    re.MULTILINE,
)


def _source_files(root: Path) -> list[Path]:
    """Return every Python source file under a directory.

    Args:
        root: Directory to walk.

    Returns:
        The files, excluding cached bytecode directories.
    """
    return [path for path in root.rglob("*.py") if "__pycache__" not in path.parts]


def _ai_source_files() -> list[Path]:
    """Return every Python source file in the ``ai`` package."""
    return _source_files(AI_PACKAGE)


def _imported_top_level_modules(source: str) -> set[str]:
    """Extract the top-level module names a source file imports.

    Only real import statements are considered; a module named inside a
    docstring or a comment is not an import and must not be reported as one.

    Args:
        source: The file's text.

    Returns:
        The set of top-level module names.
    """
    found: set[str] = set()
    for match in _IMPORT_PATTERN.finditer(source):
        raw = match.group("from") or match.group("import") or ""
        for name in raw.split(","):
            head = name.strip().split(".")[0]
            if head:
                found.add(head)
    return found


class TestAiPackageHasNoFrameworkImports:
    """NFR-M1, checked against the source text of every file in ``ai/``."""

    def test_the_package_actually_contains_source_files(self) -> None:
        """Guards the rest of this class from passing vacuously.

        A rename or a moved directory would otherwise turn every check below
        into "no files scanned, therefore no violations".
        """
        files = _ai_source_files()
        assert len(files) >= 10, f"expected the inference package, found {files}"

    @pytest.mark.parametrize("forbidden", FORBIDDEN_IN_AI)
    def test_no_file_imports_a_forbidden_module(self, forbidden: str) -> None:
        offenders: list[str] = []
        for path in _ai_source_files():
            imported = _imported_top_level_modules(
                path.read_text(encoding="utf-8", errors="replace")
            )
            if forbidden in imported:
                offenders.append(str(path.relative_to(PROJECT_ROOT)))
        assert not offenders, (
            f"NFR-M1 violated: {offenders} import {forbidden!r}. The ai package "
            "must stay independent of the service tier."
        )

    @pytest.mark.parametrize("forbidden", FORBIDDEN_IN_INFERENCE)
    def test_the_inference_tier_is_stricter_still(self, forbidden: str) -> None:
        """``ai/inference/`` additionally imports neither the ORM nor ``backend``.

        The dependency arrow points one way: ``backend`` may use ``ai``. The
        reverse would make the inference tier unusable without the server and
        turn the two into one circular unit.
        """
        offenders: list[str] = []
        for path in _source_files(INFERENCE_PACKAGE):
            imported = _imported_top_level_modules(
                path.read_text(encoding="utf-8", errors="replace")
            )
            if forbidden in imported:
                offenders.append(str(path.relative_to(PROJECT_ROOT)))
        assert not offenders, f"NFR-M1 violated: {offenders} import {forbidden!r}"

    def test_the_evaluation_harness_keeps_its_backend_imports_function_local(
        self,
    ) -> None:
        """The one place ``ai`` reaches into ``backend``, held to a condition.

        ``ai/evaluation/stress_test.py`` measures the backend, so it must import
        it. What keeps that from becoming an architectural violation is that the
        imports sit *inside functions*: importing the module pulls in nothing,
        so the evaluation package stays importable without a database. This test
        pins that condition down, since moving one import to the top of the file
        would silently remove it.
        """
        offenders: list[str] = []
        for path in _source_files(AI_PACKAGE):
            for number, line in enumerate(
                path.read_text(encoding="utf-8", errors="replace").splitlines(),
                start=1,
            ):
                if not line.startswith((" ", "\t")) and _IMPORT_PATTERN.match(line):
                    head = (_imported_top_level_modules(line) or {""}).pop()
                    if head in {"backend", "sqlalchemy"}:
                        offenders.append(
                            f"{path.relative_to(PROJECT_ROOT)}:{number}: {line.strip()}"
                        )
        assert not offenders, (
            "these imports are at module level and must be moved inside the "
            "function that needs them:\n" + "\n".join(offenders)
        )


class TestImportingAiDoesNotLoadTheFramework:
    """The same constraint, observed at runtime in a clean interpreter.

    The source scan above cannot see a transitive import: a module in ``ai``
    could import an innocuous-looking helper that itself pulls the framework in.
    This test catches that, because it inspects what actually ended up in
    ``sys.modules``.
    """

    @staticmethod
    def _run(snippet: str) -> subprocess.CompletedProcess[str]:
        """Execute a snippet in a fresh interpreter rooted at the project.

        Args:
            snippet: Python source to run.

        Returns:
            The completed process, with output captured.
        """
        return subprocess.run(
            [sys.executable, "-c", snippet],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=180,
        )

    def test_importing_the_package_pulls_in_no_forbidden_module(self) -> None:
        snippet = (
            "import sys\n"
            "import ai.inference\n"
            f"forbidden = {FORBIDDEN_IN_AI!r}\n"
            "loaded = sorted(name for name in forbidden if name in sys.modules)\n"
            "print('LOADED:' + ','.join(loaded))\n"
        )
        result = self._run(snippet)
        assert (
            result.returncode == 0
        ), f"importing ai.inference failed:\n{result.stdout}\n{result.stderr}"
        line = [row for row in result.stdout.splitlines() if row.startswith("LOADED:")]
        assert line, f"probe produced no verdict:\n{result.stdout}\n{result.stderr}"
        loaded = line[0].removeprefix("LOADED:").strip()
        assert loaded == "", f"NFR-M1 violated: importing ai.inference loaded {loaded}"

    def test_every_inference_module_imports_cleanly_on_its_own(self) -> None:
        """Each module must be importable without the rest of the world.

        Import order should not matter: a module that only works because
        another was imported first has a hidden dependency.
        """
        modules = sorted(
            f"ai.inference.{path.stem}"
            for path in (AI_PACKAGE / "inference").glob("*.py")
            if path.stem != "__init__"
        )
        snippet = (
            "import importlib, sys\n"
            f"names = {modules!r}\n"
            "for name in names:\n"
            "    importlib.import_module(name)\n"
            f"forbidden = {FORBIDDEN_IN_AI!r}\n"
            "print('LOADED:' + ','.join(sorted(n for n in forbidden if n in sys.modules)))\n"
        )
        result = self._run(snippet)
        assert (
            result.returncode == 0
        ), f"importing the inference modules failed:\n{result.stdout}\n{result.stderr}"
        loaded = result.stdout.split("LOADED:")[-1].strip()
        assert loaded == "", f"NFR-M1 violated: modules loaded {loaded}"

    def test_the_pipeline_can_be_built_from_fakes_without_an_ml_runtime(self) -> None:
        """``ALPRPipeline`` must be constructible with no model installed.

        This is dependency injection stated as a testable fact: if the class
        reached for a concrete engine, this snippet could not run.
        """
        snippet = (
            "import sys\n"
            "import numpy as np\n"
            "from ai.inference.pipeline import ALPRPipeline\n"
            "from ai.inference.interfaces import BaseDetector, BaseRecognizer, BaseNormalizer\n"
            "class D(BaseDetector):\n"
            "    @property\n"
            "    def name(self): return 'fake'\n"
            "    def detect(self, image): return []\n"
            "class R(BaseRecognizer):\n"
            "    @property\n"
            "    def name(self): return 'fake'\n"
            "    def recognize(self, plate_image): raise AssertionError\n"
            "class N(BaseNormalizer):\n"
            "    def normalize(self, raw_text): return raw_text, False\n"
            "pipeline = ALPRPipeline(detector=D(), recognizer=R(), normalizer=N())\n"
            "result = pipeline.process(np.zeros((32, 64, 3), dtype=np.uint8))\n"
            "assert result.plate_count == 0\n"
            "heavy = [n for n in ('ultralytics', 'paddleocr', 'torch') if n in sys.modules]\n"
            "print('HEAVY:' + ','.join(sorted(heavy)))\n"
        )
        result = self._run(snippet)
        assert (
            result.returncode == 0
        ), f"building the pipeline from fakes failed:\n{result.stdout}\n{result.stderr}"
        heavy = result.stdout.split("HEAVY:")[-1].strip()
        assert heavy == "", f"the pipeline pulled in an ML runtime it should not need: {heavy}"


class TestNoHardCodedPaths:
    """NFR-M4, checked where it is cheapest to violate.

    Only absolute paths written as literals are looked for. A relative path is
    fine -- both configuration modules anchor those against a root derived from
    ``__file__``.
    """

    _ABSOLUTE_LITERAL = re.compile(
        r"""["'](?:[A-Za-z]:[\\/]|/(?:home|Users|mnt|opt|var)/)""",
    )

    @pytest.mark.parametrize("package", ["ai", "backend"])
    def test_no_module_contains_an_absolute_path_literal(self, package: str) -> None:
        offenders: list[str] = []
        root = PROJECT_ROOT / package
        for path in root.rglob("*.py"):
            if "__pycache__" in path.parts or "migrations" in path.parts:
                continue
            if ".venv" in str(path):
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            for number, line in enumerate(text.splitlines(), start=1):
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                if self._ABSOLUTE_LITERAL.search(line):
                    offenders.append(f"{path.relative_to(PROJECT_ROOT)}:{number}: {stripped}")
        assert not offenders, "NFR-M4 violated by:\n" + "\n".join(offenders)

    def test_both_configuration_modules_derive_their_root_from_file(self) -> None:
        for module in (
            PROJECT_ROOT / "ai" / "inference" / "config.py",
            PROJECT_ROOT / "backend" / "core" / "config.py",
        ):
            text = module.read_text(encoding="utf-8")
            assert (
                "Path(__file__).resolve().parents" in text
            ), f"{module} should derive PROJECT_ROOT from its own location"
