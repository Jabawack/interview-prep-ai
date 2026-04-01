import { cn } from "@/lib/utils";

const SITE_CONFIG: Record<
  string,
  { label: string; icon: React.ReactNode; className: string }
> = {
  linkedin: {
    label: "LinkedIn",
    icon: (
      <svg viewBox="0 0 24 24" fill="currentColor" className="h-3 w-3">
        <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
      </svg>
    ),
    className:
      "bg-[#0A66C2]/10 text-[#0A66C2] border-[#0A66C2]/20 dark:bg-[#0A66C2]/20 dark:text-[#5B9BD5] dark:border-[#0A66C2]/30",
  },
  indeed: {
    label: "Indeed",
    icon: (
      <svg viewBox="0 0 24 24" fill="currentColor" className="h-3 w-3">
        <path d="M11.566 21.5629V8.4957c1.8824.0389 3.2461-.4848 4.1366-1.4413.8905-1.006 1.3364-2.3697 1.3364-4.1366 0-.3395-.0194-.6595-.0583-.9601C15.3478 3.4474 13.3102 4.3768 11.566 5.9855V.1746c-.9876.4654-1.878.9309-2.7878 1.493v19.8953c0 .7372.6789 1.3383 1.4025 1.3383.7237 0 1.3853-.6011 1.3853-1.3383z" />
      </svg>
    ),
    className:
      "bg-[#2164F3]/10 text-[#2164F3] border-[#2164F3]/20 dark:bg-[#2164F3]/20 dark:text-[#6B9AFF] dark:border-[#2164F3]/30",
  },
  google: {
    label: "Google",
    icon: (
      <svg viewBox="0 0 24 24" fill="currentColor" className="h-3 w-3">
        <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4" />
        <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
        <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
        <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
      </svg>
    ),
    className:
      "bg-zinc-100 text-zinc-700 border-zinc-200 dark:bg-zinc-800 dark:text-zinc-300 dark:border-zinc-700",
  },
  zip_recruiter: {
    label: "ZipRecruiter",
    icon: (
      <svg viewBox="0 0 24 24" fill="currentColor" className="h-3 w-3">
        <path d="M3 4h18l-3.5 4H6.5L3 4zm0 16h18l-3.5-4H6.5L3 20zm0-8h18v-1H3v1z" />
      </svg>
    ),
    className:
      "bg-[#6BBE45]/10 text-[#6BBE45] border-[#6BBE45]/20 dark:bg-[#6BBE45]/20 dark:text-[#8FD46A] dark:border-[#6BBE45]/30",
  },
};

export function SiteBadge({ site }: { site: string }) {
  const cfg = SITE_CONFIG[site.toLowerCase()];
  if (!cfg) {
    return (
      <span className="inline-flex items-center gap-1 rounded-full border border-zinc-200 bg-zinc-50 px-1.5 py-0.5 text-[10px] font-medium text-zinc-500 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-400">
        {site}
      </span>
    );
  }

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border px-1.5 py-0.5 text-[10px] font-medium",
        cfg.className,
      )}
    >
      {cfg.icon}
      {cfg.label}
    </span>
  );
}
