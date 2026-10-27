import type { InputHTMLAttributes } from "react";

type FormFieldProps = InputHTMLAttributes<HTMLInputElement> & {
    id: string;
    label: string;
};

export default function FormField({ id, label, ...props }: FormFieldProps) {
    return (
        <div>
            <label
                htmlFor={id}
                className="text-sm font-medium text-brand-900/80"
            >
                {label}
            </label>
            <input
                id={id}
                className="mt-1 w-full rounded-xl border border-brand-200 px-3 py-2.5 text-sm outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-500"
                {...props}
            />
        </div>
    );
}
