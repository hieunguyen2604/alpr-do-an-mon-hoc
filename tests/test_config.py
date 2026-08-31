"""Unit tests for :class:`ai.inference.config.InferenceConfig`."""

from __future__ import annotations

from pathlib import Path

import pytest

from ai.inference.config import (
    DEFAULT_ENV_PREFIX,
    PROJECT_ROOT,
    InferenceConfig,
)

_ENV_KEYS = (
    "MODEL_PATH",
    "DEVICE",
    "CONF_THRESHOLD",
    "IOU_THRESHOLD",
    "IMGSZ",
    "OCR_LANG",
    "OCR_USE_GPU",
    "TWO_LINE_ASPECT_RATIO",
)


@pytest.fixture(autouse=True)
def _clean_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove every ``ALPR_`` variable so tests never inherit a real setting."""
    for key in _ENV_KEYS:
        monkeypatch.delenv(f"{DEFAULT_ENV_PREFIX}{key}", raising=False)
        monkeypatch.delenv(f"TEST_{key}", raising=False)


class TestDefaults:
    """The configuration a caller gets with no environment at all."""

    def test_builds_without_any_environment(self) -> None:
        config = InferenceConfig.from_env()
        assert config.device == "cpu"
        assert config.conf_threshold == 0.25
        assert config.iou_threshold == 0.45
        assert config.imgsz == 640
        assert config.ocr_lang == "en"
        assert config.ocr_use_gpu is False
        assert config.two_line_aspect_ratio_threshold == 2.5

    def test_the_default_device_is_cpu(self) -> None:
        """Decision AD-06: the target machine has no CUDA GPU."""
        assert InferenceConfig().device == "cpu"
        assert InferenceConfig().ocr_use_gpu is False

    def test_geometry_retry_ships_on_and_super_resolution_ships_off(self) -> None:
        """The two rungs of the retry ladder are priced differently (28/07/2026)."""
        config = InferenceConfig()
        assert config.rectify_enabled is True
        assert config.sr_retry_enabled is False

    def test_text_detection_stays_in_the_pipeline_by_default(self) -> None:
        """Skipping PaddleOCR's detection stage ships OFF (02/08/2026)."""
        config = InferenceConfig()
        assert config.ocr_skip_detection is False

    def test_the_default_model_path_is_under_the_project_root(self) -> None:
        config = InferenceConfig()
        assert config.model_path == PROJECT_ROOT / "models" / "best.pt"
        assert config.model_path.is_absolute()

    def test_the_project_root_is_derived_not_hard_coded(self) -> None:
        """NFR-M4: the root is computed from this package's own location."""
        assert (PROJECT_ROOT / "ai" / "inference" / "config.py").is_file()


class TestPathResolution:
    """How ``ALPR_MODEL_PATH`` is interpreted."""

    def test_a_relative_path_is_anchored_to_the_project_root(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Not to the working directory -- that is the whole point."""
        monkeypatch.setenv("ALPR_MODEL_PATH", "models/custom.pt")
        config = InferenceConfig.from_env()
        assert config.model_path == PROJECT_ROOT / "models" / "custom.pt"

    def test_an_absolute_path_is_used_unchanged(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        target = tmp_path / "weights.pt"
        monkeypatch.setenv("ALPR_MODEL_PATH", str(target))
        assert InferenceConfig.from_env().model_path == target

    def test_a_relative_path_passed_directly_is_anchored_too(self) -> None:
        """The same rule applies to the constructor, not only to ``from_env``."""
        config = InferenceConfig(model_path=Path("models") / "x.pt")
        assert config.model_path == PROJECT_ROOT / "models" / "x.pt"

    def test_a_user_home_path_is_expanded(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ALPR_MODEL_PATH", "~/weights.pt")
        resolved = InferenceConfig.from_env().model_path
        assert "~" not in str(resolved)
        assert resolved.is_absolute()


class TestReadingValues:
    """Each supported variable reaches its field."""

    def test_reads_every_documented_variable(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ALPR_DEVICE", "cuda")
        monkeypatch.setenv("ALPR_CONF_THRESHOLD", "0.4")
        monkeypatch.setenv("ALPR_IOU_THRESHOLD", "0.6")
        monkeypatch.setenv("ALPR_IMGSZ", "960")
        monkeypatch.setenv("ALPR_OCR_LANG", "vi")
        monkeypatch.setenv("ALPR_OCR_USE_GPU", "true")
        monkeypatch.setenv("ALPR_TWO_LINE_ASPECT_RATIO", "3.0")

        config = InferenceConfig.from_env()

        assert config.device == "cuda"
        assert config.conf_threshold == 0.4
        assert config.iou_threshold == 0.6
        assert config.imgsz == 960
        assert config.ocr_lang == "vi"
        assert config.ocr_use_gpu is True
        assert config.two_line_aspect_ratio_threshold == 3.0

    def test_surrounding_whitespace_is_stripped(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ALPR_DEVICE", "  cuda  ")
        monkeypatch.setenv("ALPR_CONF_THRESHOLD", "  0.5  ")
        config = InferenceConfig.from_env()
        assert config.device == "cuda"
        assert config.conf_threshold == 0.5

    def test_an_empty_variable_is_treated_as_unset(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A stray ``ALPR_DEVICE=`` in a shell profile must not blank a setting."""
        monkeypatch.setenv("ALPR_DEVICE", "")
        monkeypatch.setenv("ALPR_IMGSZ", "   ")
        config = InferenceConfig.from_env()
        assert config.device == "cpu"
        assert config.imgsz == 640

    @pytest.mark.parametrize("value", ["1", "true", "TRUE", "Yes", "on", "ON"])
    def test_accepts_every_truthy_boolean_spelling(
        self, monkeypatch: pytest.MonkeyPatch, value: str
    ) -> None:
        monkeypatch.setenv("ALPR_OCR_USE_GPU", value)
        assert InferenceConfig.from_env().ocr_use_gpu is True

    @pytest.mark.parametrize("value", ["0", "false", "FALSE", "No", "off", "OFF"])
    def test_accepts_every_falsy_boolean_spelling(
        self, monkeypatch: pytest.MonkeyPatch, value: str
    ) -> None:
        monkeypatch.setenv("ALPR_OCR_USE_GPU", value)
        assert InferenceConfig.from_env().ocr_use_gpu is False

    def test_a_custom_prefix_isolates_two_configurations(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Two prefixes let a test run side by side with the real settings."""
        monkeypatch.setenv("ALPR_DEVICE", "cuda")
        monkeypatch.setenv("TEST_DEVICE", "cpu")
        assert InferenceConfig.from_env().device == "cuda"
        assert InferenceConfig.from_env(prefix="TEST_").device == "cpu"


class TestInvalidEnvironmentValuesRaise:
    """A malformed variable must fail loudly instead of falling back."""

    @pytest.mark.parametrize(
        "key", ["ALPR_CONF_THRESHOLD", "ALPR_IOU_THRESHOLD", "ALPR_TWO_LINE_ASPECT_RATIO"]
    )
    def test_a_non_numeric_float_raises(self, monkeypatch: pytest.MonkeyPatch, key: str) -> None:
        monkeypatch.setenv(key, "high")
        with pytest.raises(ValueError, match="not a valid number"):
            InferenceConfig.from_env()

    def test_a_non_integer_imgsz_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ALPR_IMGSZ", "640.5")
        with pytest.raises(ValueError, match="not a valid integer"):
            InferenceConfig.from_env()

    def test_an_unrecognised_boolean_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ALPR_OCR_USE_GPU", "maybe")
        with pytest.raises(ValueError, match="not a valid boolean"):
            InferenceConfig.from_env()

    def test_the_error_names_the_variable_and_its_value(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A configuration error that does not say *which* setting is useless."""
        monkeypatch.setenv("ALPR_CONF_THRESHOLD", "banana")
        with pytest.raises(ValueError) as raised:
            InferenceConfig.from_env()
        message = str(raised.value)
        assert "ALPR_CONF_THRESHOLD" in message
        assert "banana" in message

    def test_an_out_of_range_threshold_from_the_environment_raises(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Parsing succeeds, validation must still reject it."""
        monkeypatch.setenv("ALPR_CONF_THRESHOLD", "1.5")
        with pytest.raises(ValueError, match=r"conf_threshold"):
            InferenceConfig.from_env()

    def test_an_imgsz_that_is_not_a_multiple_of_32_raises(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("ALPR_IMGSZ", "641")
        with pytest.raises(ValueError, match="multiple of 32"):
            InferenceConfig.from_env()


class TestFieldValidation:
    """Direct construction is validated exactly as ``from_env`` is."""

    @pytest.mark.parametrize("value", [-0.1, 1.1, 2.0, -1.0])
    def test_rejects_a_confidence_outside_zero_to_one(self, value: float) -> None:
        with pytest.raises(ValueError, match=r"conf_threshold must be within"):
            InferenceConfig(conf_threshold=value)

    @pytest.mark.parametrize("value", [-0.1, 1.1])
    def test_rejects_an_iou_outside_zero_to_one(self, value: float) -> None:
        with pytest.raises(ValueError, match=r"iou_threshold must be within"):
            InferenceConfig(iou_threshold=value)

    @pytest.mark.parametrize("value", [0.0, 0.5, 1.0])
    def test_accepts_the_inclusive_bounds(self, value: float) -> None:
        config = InferenceConfig(conf_threshold=value, iou_threshold=value)
        assert config.conf_threshold == value

    @pytest.mark.parametrize("value", [0, -32, 100, 641, 33])
    def test_rejects_an_imgsz_that_is_not_a_positive_multiple_of_32(self, value: int) -> None:
        """A non-multiple is silently resized by YOLO, so the configured number"""
        with pytest.raises(ValueError, match="multiple of 32"):
            InferenceConfig(imgsz=value)

    @pytest.mark.parametrize("value", [32, 320, 640, 960, 1280])
    def test_accepts_a_positive_multiple_of_32(self, value: int) -> None:
        assert InferenceConfig(imgsz=value).imgsz == value

    @pytest.mark.parametrize("value", [0.0, -1.0])
    def test_rejects_a_non_positive_aspect_ratio(self, value: float) -> None:
        with pytest.raises(ValueError, match="two_line_aspect_ratio_threshold"):
            InferenceConfig(two_line_aspect_ratio_threshold=value)

    def test_rejects_an_empty_device(self) -> None:
        with pytest.raises(ValueError, match="device must be a non-empty string"):
            InferenceConfig(device="")

    def test_rejects_an_empty_ocr_language(self) -> None:
        with pytest.raises(ValueError, match="ocr_lang must be a non-empty string"):
            InferenceConfig(ocr_lang="")


class TestFineTunedRecModelDir:
    """The opt-in path to a fine-tuned recognition model (ai/training)."""

    def test_defaults_to_none(self) -> None:
        assert InferenceConfig().ocr_rec_model_dir is None

    def test_an_existing_directory_is_accepted_and_normalised(self, tmp_path: Path) -> None:
        config = InferenceConfig(ocr_rec_model_dir=tmp_path)
        assert config.ocr_rec_model_dir == tmp_path

    def test_a_missing_directory_fails_at_startup(self, tmp_path: Path) -> None:
        """A mistyped path must fail loudly, not silently use stock weights."""
        with pytest.raises(ValueError, match="ocr_rec_model_dir"):
            InferenceConfig(ocr_rec_model_dir=tmp_path / "khong-ton-tai")

    def test_read_from_the_environment(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("ALPRTEST_OCR_REC_MODEL_DIR", str(tmp_path))
        config = InferenceConfig.from_env(prefix="ALPRTEST_")
        assert config.ocr_rec_model_dir == tmp_path

    def test_unset_environment_means_stock_weights(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("ALPRTEST_OCR_REC_MODEL_DIR", raising=False)
        assert InferenceConfig.from_env(prefix="ALPRTEST_").ocr_rec_model_dir is None


class TestConfigurationIsInjectable:
    """The dataclass is what makes the pipeline testable without the environment."""

    def test_a_test_can_build_exactly_the_configuration_it_needs(self, tmp_path: Path) -> None:
        config = InferenceConfig(
            model_path=tmp_path / "w.pt",
            device="cpu",
            conf_threshold=0.9,
            imgsz=320,
        )
        assert config.model_path == tmp_path / "w.pt"
        assert config.conf_threshold == 0.9
        assert config.imgsz == 320

    def test_two_instances_are_independent(self) -> None:
        first = InferenceConfig(conf_threshold=0.1)
        second = InferenceConfig(conf_threshold=0.9)
        assert first.conf_threshold == 0.1
        assert second.conf_threshold == 0.9
