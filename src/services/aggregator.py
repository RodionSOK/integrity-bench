from src.core.detectors.base import DetectorResult

class Aggregator:
    INTACT_THRESHOLD = 0.8
    CORRUPTED_THRESHOLD = 0.3
    HIGH_CONFIDENCE_THRESHOLD = 0.9

    def aggregate(self, results: list[DetectorResult]) -> dict:
        applicable = [r for r in results if r.applicable]
        if not applicable:
            return {'score': 0.5, 'label': 'uncertain'}


        high_conf = [r for r in applicable if r.confidence >= self.HIGH_CONFIDENCE_THRESHOLD]
        if high_conf:
            best = max(high_conf, key=lambda r: r.confidence)
            score = best.score
        else:
            total_w = sum(r.confidence for r in applicable)
            score = sum(r.score * r.confidence for r in applicable) / total_w

        if score >= self.INTACT_THRESHOLD:
            label = 'intact'
        elif score <= self.CORRUPTED_THRESHOLD:
            label = 'corrupted'
        else:
            label = 'uncertain'

        return {'score': round(score, 4), 'label': label}
