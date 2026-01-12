
import DashboardLayout from "@/components/DashboardLayout";

export default function Layout({
    children,
    params
}: {
    children: React.ReactNode,
    params: any
}) {
    return (
        <DashboardLayout params={params}>
            {children}
        </DashboardLayout>
    );
}
