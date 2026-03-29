import Link from "next/link";

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-6">
      <h1 className="text-3xl font-bold">InterviewPrepAI</h1>
      <p className="max-w-md text-center text-zinc-500">
        AI-powered interview preparation — find jobs, research companies,
        practice questions, and ace your next interview.
      </p>
      <Link
        href="/chat"
        className="rounded-lg bg-blue-600 px-6 py-2.5 text-sm font-medium text-white hover:bg-blue-700"
      >
        Start Preparing
      </Link>
    </div>
  );
}
