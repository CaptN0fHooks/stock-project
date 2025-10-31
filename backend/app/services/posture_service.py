import statistics
from typing import Dict, List
from app.models import SessionPosture, PostureComponents

class PostureService:
    """Calculate Session Posture heuristic"""

    @staticmethod
    def calculate(breadth: Dict, sectors: List[Dict], vix_data: Dict) -> SessionPosture:
        """
        Score = 0.4 * Breadth + 0.4 * Dispersion + 0.2 * VIX_Overlay
        Returns a SessionPosture pydantic model.
        """
        breadth_score = PostureService._calc_breadth(breadth)
        dispersion_score = PostureService._calc_dispersion(sectors)
        vix_score = PostureService._calc_vix_overlay(vix_data)

        final_score = 0.4 * breadth_score + 0.4 * dispersion_score + 0.2 * vix_score

        if final_score >= 30:
            label = "Risk-On"
        elif final_score <= -30:
            label = "Risk-Off"
        else:
            label = "Neutral"

        notes = [
            f"Breadth: {breadth_score:.1f}/100 (40% weight)",
            f"Sector Dispersion: {dispersion_score:.1f}/100 (40% weight)",
            f"VIX Overlay: {vix_score:.1f}/100 (20% weight)",
            "Formula: Score = 0.4×Breadth + 0.4×Dispersion + 0.2×VIX",
        ]

        return SessionPosture(
            score=round(final_score, 1),
            label=label,
            components=PostureComponents(
                breadth=round(breadth_score, 1),
                dispersion=round(dispersion_score, 1),
                vol_overlay=round(vix_score, 1),
            ),
            notes=notes,
        )

    @staticmethod
    def _calc_breadth(breadth: Dict) -> float:
        """Calculate breadth component (-100..+100). If missing data, return 0."""
        nyse = breadth.get("nyse", {}) if isinstance(breadth, dict) else {}
        nasdaq = breadth.get("nasdaq", {}) if isinstance(breadth, dict) else {}

        nyse_adv = nyse.get("advancers")
        nyse_dec = nyse.get("decliners")
        nasdaq_adv = nasdaq.get("advancers")
        nasdaq_dec = nasdaq.get("decliners")

        # If any piece is missing/None/0, treat as unavailable
        if not all(x is not None and x >= 0 for x in [nyse_adv, nyse_dec, nasdaq_adv, nasdaq_dec]):
            return 0.0

        def ratio(adv, dec):
            total = (adv or 0) + (dec or 0)
            return ((adv - dec) / total) if total > 0 else 0.0

        nyse_ratio = ratio(nyse_adv, nyse_dec)
        nasdaq_ratio = ratio(nasdaq_adv, nasdaq_dec)

        return ((nyse_ratio + nasdaq_ratio) / 2.0) * 100.0

    @staticmethod
    def _calc_dispersion(sectors: List[Dict]) -> float:
        """Calculate sector dispersion (-100..+100). Robust to missing/empty."""
        if not sectors:
            return 0.0

        returns: List[float] = []
        for s in sectors:
            try:
                returns.append(float(s.get("pct", 0.0) or 0.0))
            except Exception:
                returns.append(0.0)

        positive_count = sum(1 for r in returns if r > 0)

        try:
            dispersion = statistics.stdev(returns) if len(returns) > 1 else 0.0
        except Exception:
            dispersion = 0.0

        HIGH_PARTICIPATION = 8   # out of ~11 sectors
        LOW_PARTICIPATION = 3
        LOW_DISPERSION = 1.5
        HIGH_DISPERSION = 3.0

        if positive_count >= HIGH_PARTICIPATION and dispersion <= LOW_DISPERSION:
            return 100.0
        if positive_count <= LOW_PARTICIPATION or dispersion >= HIGH_DISPERSION:
            return -100.0

        # Interpolate between bounds
        part_score = ((positive_count - LOW_PARTICIPATION) / max(1, (HIGH_PARTICIPATION - LOW_PARTICIPATION))) * 100.0
        part_score = max(-100.0, min(100.0, part_score))

        disp_score = ((HIGH_DISPERSION - dispersion) / max(1e-6, (HIGH_DISPERSION - LOW_DISPERSION))) * 100.0
        disp_score = max(-100.0, min(100.0, disp_score))

        return (part_score + disp_score) / 2.0

    @staticmethod
    def _calc_vix_overlay(vix_data: Dict) -> float:
        """Calculate VIX overlay (-100..+100). Accepts dict or (dict, source)."""

        # Normalize input: accept dict or (data, source)
        if isinstance(vix_data, (list, tuple)):
            vix_data = vix_data[0] if vix_data else {}
        if vix_data is None or not isinstance(vix_data, dict):
            vix_data = {}

        try:
            vix_pct = float(vix_data.get("pct", 0.0) or 0.0)
        except Exception:
            vix_pct = 0.0

        # Heuristic buckets
        if vix_pct <= -5:
            return 100.0
        if -5 < vix_pct <= -2:
            return 50.0
        if -2 < vix_pct < 2:
            return 0.0
        if 2 <= vix_pct < 5:
            return -50.0
        return -100.0
