import itertools

PERIODS = {
    "1927-1940": ("1927-01-01", "1940-12-31"),
    "1940-1950": ("1940-01-01", "1950-12-31"),
    "1950-1960": ("1950-01-01", "1960-12-31"),
    "1960-1970": ("1960-01-01", "1970-12-31"),
    "1970-1980": ("1970-01-01", "1980-12-31"),
    "1980-1990": ("1980-01-01", "1990-12-31"),
    "1990-2000": ("1990-01-01", "2000-12-31"),
    "2000-2010": ("2000-01-01", "2010-12-31"),
    "2010-2020": ("2010-01-01", "2020-12-31"),
    "2020-2026": ("2020-01-01", "2026-12-31"),
}

t_x2_30_x3_70 = {
    -0.10: (0.05, "x2"),
    -0.15: (0.15, "x2"),
    -0.20: (0.30, "x2"),
    -0.30: (0.10, "x3"),
    -0.40: (0.30, "x3"),
    -0.50: (0.50, "x3"),
    -0.60: (0.70, "x3"),
}

t_x2_50_x3_50 = {
    -0.10: (0.05, "x2"),
    -0.20: (0.25, "x2"),
    -0.30: (0.50, "x2"),
    -0.40: (0.20, "x3"),
    -0.50: (0.40, "x3"),
    -0.60: (0.50, "x3"),
}

t_robust_optimal = {
    # Low corrections
    -0.05: (0.05, "x1"),
    -0.10: (0.10, "x1"),
    -0.15: (0.10, "x2"),

    # Serious corrections
    -0.25: (0.20, "x2"),

    # Crisis
    -0.35: (0.10, "x3"),
    -0.45: (0.30, "x3"),
    -0.55: (0.50, "x3"),
    -0.65: (0.70, "x3"),
}


t_crisis_only = {
    -0.30: (0.30, "x2"),
    -0.40: (0.30, "x3"),
    -0.50: (0.70, "x3"),
}

t_x2_100 = {
    -0.10: (0.05, "x2"),
    -0.15: (0.15, "x2"),
    -0.20: (0.30, "x2"),
    -0.30: (0.40, "x2"),
    -0.40: (0.50, "x2"),
    -0.50: (0.70, "x2"),
    -0.60: (1.00, "x2"),
}

t_x1_100 = {
    -0.10: (0.05, "x1"),
    -0.15: (0.15, "x1"),
    -0.20: (0.30, "x1"),
    -0.30: (0.40, "x1"),
    -0.40: (0.50, "x1"),
    -0.50: (0.70, "x1"),
    -0.60: (1.00, "x1"),
}

ENTRY_THRESHOLDS_SPACE = {
    "x2_30_x3_70": t_x2_30_x3_70,
    "x2_50_x3_50": t_x2_50_x3_50,
    "robust_optimal": t_robust_optimal,
    "crisis_only": t_crisis_only,
    "x2_100": t_x2_100,
    "x1_100": t_x1_100
}


YIELD_TARGETS_SPACE = {
    "x1": ["auto", "num", "none"],
    "x2": ["auto", "num", "none"],
    "x3": ["auto", "num", "none"],
}
YIELD_VALUES_SPACE = [0.25, 0.5, 0.75, 1.0]  # only if yield_target == "num"
ROTATE_SPACE = [True, False]


def _is_valid_config(assets, yield_targets, yield_values, rotate):

    # Rotations are only supported between "x2" and "x3"
    if rotate and "x3" not in assets and "x2" not in assets:
        return False

    # When yield target is "num" yield values must be a number between 0 and 1
    for asset, target in yield_targets.items():
        if target == "num":
            v = yield_values.get(asset)
            if v is None or not (0 < v <= 1):
                return False
        else:
            v = yield_values.get(asset)
            if v is not None:
                return False

    return True


def _build_config_name(entry_name, yield_targets, yield_values, rotate):
    parts = [f"T[{entry_name}]"]

    yt = []
    for a, t in yield_targets.items():
        if t == "num":
            yt.append(f"{a}:{t}{int(yield_values[a]*100)}")
        else:
            yt.append(f"{a}:{t}")

    parts.append("Y[" + ",".join(sorted(yt)) + "]")
    parts.append("R" if rotate else "NR")

    return " | ".join(parts)


def build_all_configurations():
    all_configs = {}
    for et_name, entry_thresholds in ENTRY_THRESHOLDS_SPACE.items():
        assets = sorted({asset for _, asset in entry_thresholds.values()})

        # 1. Yield target
        per_asset_targets = []
        for asset in assets:
            allowed = YIELD_TARGETS_SPACE.get(asset, [])
            # e.g., [('x2', 'auto'), ('x2', 'num'), ('x2', 'none')]
            per_asset_targets.append([(asset, yt) for yt in allowed])

        for targets_combo in itertools.product(*per_asset_targets):
            yield_targets = dict(targets_combo)
            # e.g., {'x2', 'auto'}, {'x3', 'num'}

            # 2. Yield values (only where target == "num")
            per_asset_values = []
            for asset, target in yield_targets.items():
                if target == "num":
                    per_asset_values.append([(asset, v) for v in YIELD_VALUES_SPACE])
                else:
                    per_asset_values.append([(asset, None)])

            for values_combo in itertools.product(*per_asset_values):
                yield_values = dict(values_combo)
                # e.g., {'x2', None}, {'x3', 0.75}

                # 3. Rotation
                for rotate in ROTATE_SPACE:

                    # Check if configuration is valid
                    if not _is_valid_config(assets, yield_targets, yield_values, rotate):
                        continue

                    # Assign a descriptive name for config
                    config_name = _build_config_name(et_name, yield_targets, yield_values, rotate)

                    all_configs[config_name] = {
                        "thresholds": entry_thresholds,
                        "yield_targets": yield_targets,
                        "yield_values": yield_values,
                        "rotate": rotate,
                    }

    return all_configs
