export default function PageStub({
    title,
    task,
    owner,
}: {
    title: string;
    task?: string;
    owner?: string;
}) {
    return (
        <main className="mx-auto max-w-xl px-4 py-16 text-center">
            <h1 className="mb-2 font-display text-2xl font-bold text-brand-900">
                {title}
            </h1>
            <p className="text-sm text-brand-900/50">
                TODO — {task ? `${task}, ` : ""}
                {owner || "unassigned"}
            </p>
        </main>
    );
}
