// Generic placeholder so every route renders something before its owner builds it.
// Delete this file's usage once a page has real content — see docs/part2 LLD 5
// (Frontend Component Breakdown) for the route table and docs/part2/backlog.md
// for the task/owner each page maps to.
export default function PageStub({ title, task, owner }) {
  return (
    <div className="max-w-xl mx-auto px-4 py-16 text-center">
      <h1 className="font-display text-2xl font-bold text-brand-900 mb-2">{title}</h1>
      <p className="text-brand-900/50 text-sm">
        TODO — {task ? `${task}, ` : ""}{owner || "unassigned"}
      </p>
    </div>
  );
}
