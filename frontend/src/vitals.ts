import { onCLS, onINP, onLCP, onFCP, onTTFB } from "web-vitals";

type MetricHandler = (metric: { name: string; value: number; id: string }) => void;

const reportMetric: MetricHandler = (metric) => {
  console.debug("[web-vitals]", metric.name, metric.value.toFixed(2));
};

export function reportWebVitals() {
  onCLS(reportMetric);
  onINP(reportMetric);
  onLCP(reportMetric);
  onFCP(reportMetric);
  onTTFB(reportMetric);
}
