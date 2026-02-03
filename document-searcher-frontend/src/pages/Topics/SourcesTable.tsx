import Dropdown from "../../components/Dropdown";
import Button   from "../../components/Button";

interface Item {
  name: string;
  display: string;
}
interface Source {
  id: string;
  name: string;
  site: string;
  schedule: string;
}

interface Props {
  loading: boolean;
  error: string | null;
  sources: Source[];
  hours: Item[];
  onScheduleChange: (id: string, val: string) => void;
  onRemove: (name: string, id: string) => void;
}

export default function SourcesTable({
  loading,
  error,
  sources,
  hours,
  onScheduleChange,
  onRemove,
}: Props) {
  if (loading) return <p>Loading…</p>;
  if (error)   return <p className="text-red-600">Error: {error}</p>;

  return (
    <div className="mt-4">
      <div className="rounded-md overflow-hidden">
        {/* header */}
        <div className="hidden md:flex bg-gray-50 px-4 py-2 text-xs font-semibold text-gray-600 uppercase" style={{background: "#024A59", color: "#ffffff"}}>
          <div className="flex-1 text-left">Name</div>
          <div className="w-48 text-center">Schedule</div>
          <div className="w-48 text-center">Site</div>
          <div className="w-60 text-center">Control</div>
        </div>

        {/* rows (scrollable) */}
        <div className="divide-y divide-gray-200 max-h-[50vh] overflow-y-auto">
          {sources.length === 0 ? (
            <div className="px-4 py-3 text-sm">No sources found.</div>
          ) : (
            sources.map((s) => (
              <div key={s.id} className="flex items-center px-4 py-3">
                <div className="flex-1 font-medium text-left">{s.name}</div>

                <div className="w-48 text-center">
                  <Dropdown
                    source={hours}
                    defaultValue={s.schedule}
                    onChange={(val) => onScheduleChange(s.id, val)}
                  />
                </div>

                <div className="w-48 text-center">
                  <span className="text-xs px-2 py-0.5 rounded bg-slate-200 uppercase" style={{background: "#024A59", color: "#ffffff"}}>
                    {
                      ({ onedrive: "Onedrive", sharepoint: "Sharepoint", googledrive: "GoogleDrive" }[
                        (s.site || "").toLowerCase()
                      ] ?? "Localfile")
                    }
                  </span>
                </div>

                <div className="w-60 text-center" style={{display: "flex", justifyContent: "center"}}>
                  <Button
                    text="Remove"
                    onClick={() => onRemove(s.name, s.id)}
                    type="CANCEL"
                    icon="remove"
                  />
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
