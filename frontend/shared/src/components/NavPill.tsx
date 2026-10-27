import {
    NavLink,
    type NavLinkProps,
    type NavLinkRenderProps,
} from "react-router-dom";

const linkClass = ({ isActive }: NavLinkRenderProps) =>
    `rounded-full px-3 py-2 text-sm font-medium ${
        isActive
            ? "bg-brand-50 text-brand-700"
            : "text-brand-900/60 hover:bg-brand-50"
    }`;

export default function NavPill(props: Omit<NavLinkProps, "className">) {
    return <NavLink {...props} className={linkClass} />;
}
