// See frontend/storefront/src/pages/PageStub.jsx for the full note.
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
