import { Link } from "react-router-dom";
import { LoginPage as SharedLoginPage } from "@ofs/shared/components";

export default function LoginPage() {
    return (
        <SharedLoginPage
            title="Welcome to OFS"
            subtitle="Organic groceries, delivered by robot."
            defaultRedirect="/browse"
            footer={
                <p className="text-center text-sm text-brand-900/60">
                    No account?{" "}
                    <Link
                        to="/register"
                        className="font-medium text-brand-700 hover:underline"
                    >
                        Register
                    </Link>
                </p>
            }
        />
    );
}
