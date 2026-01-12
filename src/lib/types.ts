export interface ProjectStatus {
    id?: string;
    client_name: string;
    project_name: string;
    status: 'planning' | 'building' | 'testing' | 'live' | string;
    progress_percent: number;
    current_phase: string;
    next_milestone: string;
    last_updated: string;
    blueprint_path?: string | null;
}
