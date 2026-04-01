import { ExternalLink, MapPin, DollarSign } from "lucide-react";

import type { JobResult } from "@/types";
import { SiteBadge } from "./SiteBadge";

export function JobCards({ jobs }: { jobs: JobResult[] }) {
  if (!jobs.length) return null;

  return (
    <div className="space-y-2">
      <p className="text-sm font-semibold text-zinc-700 dark:text-zinc-300">
        Found {jobs.length} job(s):
      </p>
      {jobs.slice(0, 10).map((job, i) => (
        <div
          key={job.url ?? i}
          className="rounded-lg border border-zinc-200 bg-white p-3 dark:border-zinc-700 dark:bg-zinc-900"
        >
          <div className="flex items-start justify-between gap-2">
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <h3 className="truncate text-sm font-semibold text-zinc-900 dark:text-zinc-100">
                  {job.title}
                </h3>
                {job.site && <SiteBadge site={job.site} />}
              </div>
              <p className="mt-0.5 text-sm text-zinc-600 dark:text-zinc-400">
                {job.company}
              </p>
            </div>
            {job.url && (
              <a
                href={job.url}
                target="_blank"
                rel="noopener noreferrer"
                className="shrink-0 rounded p-1 text-zinc-400 transition-colors hover:bg-zinc-100 hover:text-zinc-600 dark:hover:bg-zinc-800 dark:hover:text-zinc-300"
              >
                <ExternalLink className="h-3.5 w-3.5" />
              </a>
            )}
          </div>
          <div className="mt-1.5 flex flex-wrap items-center gap-3 text-xs text-zinc-500 dark:text-zinc-400">
            {job.location && (
              <span className="flex items-center gap-1">
                <MapPin className="h-3 w-3" />
                {job.location}
              </span>
            )}
            {job.salary && job.salary !== "nan-nan" && (
              <span className="flex items-center gap-1">
                <DollarSign className="h-3 w-3" />
                {job.salary}
              </span>
            )}
            {job.date_posted && job.date_posted !== "NaT" && (
              <span>{job.date_posted}</span>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
