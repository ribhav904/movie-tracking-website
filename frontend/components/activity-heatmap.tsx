import { eachDayOfInterval, endOfYear, format, startOfYear } from "date-fns";

import type { DailyActivity } from "@/lib/types";

export function ActivityHeatmap({ year, calendar }: { year: number; calendar: DailyActivity[] }) {
  const counts = new Map(calendar.map((item) => [item.date, item.count]));
  const days = eachDayOfInterval({ start: startOfYear(new Date(year, 0, 1)), end: endOfYear(new Date(year, 0, 1)) });
  return (
    <div className="heatmap" role="img" aria-label={`${calendar.length} active days in ${year}`}>
      <div className="heatmap__months" aria-hidden="true"><span>Jan</span><span>Mar</span><span>May</span><span>Jul</span><span>Sep</span><span>Nov</span></div>
      <div className="heatmap__grid">
        {days.map((day) => {
          const key = format(day, "yyyy-MM-dd");
          const count = counts.get(key) ?? 0;
          return <span key={key} className={`heatmap__day heatmap__day--${Math.min(count, 4)}`} title={`${format(day, "d MMMM")}: ${count} activities`} />;
        })}
      </div>
      <div className="heatmap__legend"><span>Less</span>{[0, 1, 2, 3, 4].map((level) => <i key={level} className={`heatmap__day heatmap__day--${level}`} />)}<span>More</span></div>
    </div>
  );
}
