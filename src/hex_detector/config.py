"""Central configuration for hex face detection."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class HexDetectorConfig:
    """All tunable parameters — no magic numbers elsewhere."""

    # ROI / bbox
    bbox_padding_ratio: float = 0.08
    bbox_ema_alpha: float = 0.35
    block_crop_bottom_ratio: float = 0.22

    # Preprocessing
    clahe_clip_limit: float = 2.0
    clahe_tile_grid_size: tuple[int, int] = (8, 8)
    gaussian_kernel: tuple[int, int] = (5, 5)
    gaussian_sigma: float = 1.2
    canny_low: int = 40
    canny_high: int = 120
    morph_kernel_size: int = 3
    morph_iterations: int = 1

    # HoughLinesP
    hough_rho: float = 1.0
    hough_theta_deg: float = 1.0
    hough_threshold: int = 30
    hough_min_line_length_ratio: float = 0.12
    hough_max_line_gap: int = 8

    # Line filtering
    min_line_length_px: int = 18
    roi_edge_margin_ratio: float = 0.04
    pallet_line_bottom_ratio: float = 0.55
    pallet_line_angle_tol_deg: float = 12.0

    # Angle grouping (degrees, normalized 0–180)
    vertical_angle_center: float = 90.0
    vertical_angle_tol_deg: float = 22.0
    front_horizontal_angle_tol_deg: float = 28.0
    right_diagonal_angle_tol_deg: float = 35.0
    front_horizontal_target_deg: float = 0.0
    right_diagonal_target_deg: float = 55.0

    # Line merge
    merge_angle_tol_deg: float = 8.0
    merge_distance_tol_ratio: float = 0.06
    max_lines_per_group: int = 6

    # Candidate search
    max_candidates: int = 48
    max_front_candidates: int = 24
    max_right_candidates: int = 24

    # Validation
    min_front_area_ratio: float = 0.08
    min_right_width_ratio: float = 0.06
    rectangle_mode_right_width_ratio: float = 0.10
    parallel_tol_deg: float = 12.0
    point_inside_margin_px: int = 2

    # Scoring weights (sum = 1.0)
    weight_edge_support: float = 0.40
    weight_parallelism: float = 0.20
    weight_topology: float = 0.20
    weight_area_position: float = 0.10
    weight_temporal: float = 0.10
    accept_score_threshold: float = 0.52
    min_edge_support_score: float = 0.15

    # Temporal
    point_ema_alpha: float = 0.45
    max_hold_frames: int = 3
    hold_iou_threshold: float = 0.5
    hold_score_decay: float = 0.8
    hold_bbox_center_jump_ratio: float = 0.3
    hold_bbox_size_change_ratio: float = 0.5
    hold_point_conflict_threshold: float = 0.3

    # Debug
    debug_draw_raw_lines: bool = True
    debug_draw_selected_lines: bool = True
    debug_mode: str = "basic"
    debug_top_candidates: int = 5

    def validate(self) -> None:
        total = (
            self.weight_edge_support
            + self.weight_parallelism
            + self.weight_topology
            + self.weight_area_position
            + self.weight_temporal
        )
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"Score weights must sum to 1.0, got {total}")
        if self.max_candidates <= 0:
            raise ValueError(f"max_candidates must be positive, got {self.max_candidates}")
        if self.max_front_candidates <= 0:
            raise ValueError(f"max_front_candidates must be positive, got {self.max_front_candidates}")
        if self.max_right_candidates <= 0:
            raise ValueError(f"max_right_candidates must be positive, got {self.max_right_candidates}")
        if not 0.0 <= self.min_edge_support_score <= 1.0:
            raise ValueError(
                f"min_edge_support_score must be in [0, 1], got {self.min_edge_support_score}"
            )
        if not 0.0 <= self.accept_score_threshold <= 1.0:
            raise ValueError(
                f"accept_score_threshold must be in [0, 1], got {self.accept_score_threshold}"
            )
        if not 0.0 <= self.hold_iou_threshold <= 1.0:
            raise ValueError(
                f"hold_iou_threshold must be in [0, 1], got {self.hold_iou_threshold}"
            )
        if not 0.0 < self.hold_score_decay < 1.0:
            raise ValueError(
                f"hold_score_decay must be in (0, 1), got {self.hold_score_decay}"
            )
        if self.max_hold_frames <= 0:
            raise ValueError(
                f"max_hold_frames must be positive, got {self.max_hold_frames}"
            )
        if self.debug_mode not in ("basic", "verbose"):
            raise ValueError(
                f"debug_mode must be 'basic' or 'verbose', got {self.debug_mode}"
            )
        if self.debug_top_candidates <= 0:
            raise ValueError(
                f"debug_top_candidates must be positive, got {self.debug_top_candidates}"
            )


DEFAULT_CONFIG = HexDetectorConfig()
