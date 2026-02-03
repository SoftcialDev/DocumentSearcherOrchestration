import  { useEffect } from 'react';
import IconButton from "../../components/IconButton";
import useDrivePicker from 'react-google-drive-picker';
import { useAuth } from "../../providers/AuthProvider";

interface PickerProps{
  topic: string;
  onPicked: () => void;
}

export default function GoogleDrivePicker({topic, onPicked}: PickerProps) {
  const returnTo = encodeURIComponent(window.location.href);
  const [openPicker, authResponse] = useDrivePicker();  
  const { account, apiFetch } = useAuth();
  // const customViewsArray = [new google.picker.DocsView()]; // custom view
  const handleOpenPicker = () => {
    openPicker({
      clientId: "359262190112-rm1r5iluanvucpnsf1f4oj6splumumnd.apps.googleusercontent.com",
      developerKey: "AIzaSyAGLfSSxS6527OeE0zHZOW46aDK1C28Fc0",
      viewId: "FOLDERS",
      showUploadView: true,
      showUploadFolders: true,
      supportDrives: true,
      multiselect: true,
      setSelectFolderEnabled: true,
      callbackFunction: (data: any) => {
        if (data?.action === "cancel") return;

        const docs = Array.isArray(data?.docs) ? data.docs : [];
        if (!docs.length) return;

        (async () => {
          // Only keep folders (defensive)
          const folders = docs.filter((d: any) =>
            d?.mimeType === "application/vnd.google-apps.folder"
          );

          const sources = folders.map((it: any) => ({
            name: it.name ?? "",           // folder name
            sharepoint_site: "",           // blank as requested
            sharepoint_list: "",           // blank as requested
            sharepoint_item: it.id ?? "",  // folder ID
          }));

          const payload = {
            topic,             // your variable from scope
            uid: account?.username,
            site: "GoogleDrive",
            sources,               // <-- matches your OneDrive payload keys
          };

          try {
            const res = await apiFetch("/api/sources/add-source", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(payload),
            });
            const data = await res.json(); 
            onPicked();
          } catch (err) {
            console.error("Failed to add sources:", err);
          }
        })();
      }
    })
  }

  return (
    <IconButton
      iconSvg='<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path fill-rule="evenodd" clip-rule="evenodd" d="M5 1C3.93913 1 2.92172 1.42143 2.17157 2.17157C1.42143 2.92172 1 3.93913 1 5V19C1 20.0609 1.42143 21.0783 2.17157 21.8284C2.92172 22.5786 3.93913 23 5 23H19C20.0609 23 21.0783 22.5786 21.8284 21.8284C22.5786 21.0783 23 20.0609 23 19V5C23 3.93913 22.5786 2.92172 21.8284 2.17157C21.0783 1.42143 20.0609 1 19 1H5ZM15.183 13.639L10.316 5.175H14.408C14.53 5.175 14.643 5.24 14.704 5.345L19.488 13.639H15.183ZM11.144 9.625L9.02 5.93L4.553 14.226C4.52698 14.2741 4.51295 14.3277 4.51208 14.3824C4.51121 14.437 4.52353 14.4911 4.548 14.54L6.281 18.007L11.144 9.624V9.625ZM17.138 18.825H7.541L9.68 15.139H19.484L17.433 18.656C17.403 18.7076 17.3599 18.7504 17.3081 18.78C17.2564 18.8097 17.1977 18.8252 17.138 18.825Z" fill="white"/></svg>'
      alt="Add topic"
      size={24}
      onClick={handleOpenPicker}
      name="GoogleDrive"
    />
  );
}

