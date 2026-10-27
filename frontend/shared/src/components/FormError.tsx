export default function FormError({ message }: { message?: string | null }) {
    if (!message) return null;

    return (
        <p className="flex items-center gap-1.5 text-sm text-red-600" role="alert">
            <i className="ph ph-warning-circle" aria-hidden="true" />
            <span>{message}</span>
        </p>
    );
}
