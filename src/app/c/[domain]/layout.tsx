
import DashboardLayout from "@/components/DashboardLayout";

export default async function Layout({
    children,
    params
}: {
    children: React.ReactNode,
    params: Promise<{ domain: string }>
}) {
    const resolvedParams = await params;
    return (
        <DashboardLayout params={resolvedParams}>
            {children}
        </DashboardLayout>
    );
}
