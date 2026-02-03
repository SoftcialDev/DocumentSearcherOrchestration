import { v4 as uuid } from "uuid";
import { useMsal } from "@azure/msal-react";
import Button from "../../components/Button";
import IconButton from "../../components/IconButton";
import { useAuth } from "../../providers/AuthProvider";

interface PickerProps{
  topicName: string;
  onPicked: () => void;
}


export default function OneDriveFolderPicker({topicName, onPicked}: PickerProps) {
  const { instance, accounts } = useMsal();
  const { apiFetch } = useAuth();

  const handlePick = async (topic: string, items: any[]) => {
    if (!items.length) return;

    /* build the sources array */
    const sources = items.map((it: any) => {
      const ids = it.parentReference?.sharepointIds ?? it.sharepointIds ?? {};
      return {
        name: it.name,
        sharepoint_site: ids.siteId,          // stays the same
        sharepoint_list: ids.listId,          // stays the same
        sharepoint_item: ids.listItemUniqueId ?? it.id  // 👈 NEW: unique per folder
      };
    });

    const payload = {
      topic,
      site: "OneDrive",
      sources,
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
  };


  async function openPicker() {
    const channelId = uuid();

    /* ▼ 1.  Only change this block ▼ */
    const pickerOptions = {
      sdk: "8.0",
      entry: {                     // ← OneDrive instead of SharePoint
        oneDrive: {},              // "My files" root
      },
      authentication: {},
      messaging: { origin: window.location.origin, channelId },
      typesAndSources: { mode: "folders", filters: ["folder"] },
      selection: { mode: "multiple" },
    };
    /* ▲ 1.  Only change this block ▲ */

    /* 2.  Use tenant‑my.sharepoint.com */
    const tenant = "softcial";   // <- your tenant short name
    const baseUrl = `https://${tenant}-my.sharepoint.com`;

    const pickerUrl =
      `${baseUrl}/_layouts/15/FilePicker.aspx?` +
      new URLSearchParams({
        filePicker: JSON.stringify(pickerOptions),
        locale: "es-es",
      });

    /* ─ popup & POST stay the same ─ */
    const win = window.open("", `_picker_${channelId}`, "width=1080,height=680");
    const doc = win!.document;
    const form = doc.createElement("form");
    form.method = "POST";
    form.action = pickerUrl;

    /* initial token for OneDrive root */
    const { accessToken } = await instance.acquireTokenSilent({
      account: accounts[0],
      scopes: [`${baseUrl}/.default`],   // SharePoint.MyFiles.* permissions
    });

    const tokenInput = doc.createElement("input");
    tokenInput.type = "hidden";
    tokenInput.name = "access_token";
    tokenInput.value = accessToken;
    form.appendChild(tokenInput);
    doc.body.appendChild(form);
    form.submit();

    /* message channel – unchanged except for dynamic tokens */
    function hostListener(evt: MessageEvent) {
      if (evt.source !== win) return;
      const msg = evt.data;
      if (msg.type === "initialize" && msg.channelId === channelId) {
        const port: MessagePort = evt.ports[0];
        port.start();
        port.postMessage({ type: "activate" });

        port.onmessage = async (e) => {
          const { id, type, data } = e.data;
          if (type !== "command") return;
          port.postMessage({ type: "acknowledge", id });

          switch (data.command) {
            case "authenticate":
              try {
                const resource = data.resource;      // e.g. https://tenant‑my.sharepoint.com
                const t = await instance.acquireTokenSilent({
                  account: accounts[0],
                  scopes: [`${resource}/.default`],
                });
                port.postMessage({
                  type: "result",
                  id,
                  data: { result: "token", token: t.accessToken },
                });
              } catch (err) {
                console.error(err);
              }
              break;

            case "pick": {
              const items = data.items ?? [];
              handlePick(topicName, items);
              port.postMessage({
                type: "result",
                id,
                data: { result: "success" },
              });
              win?.close();
              window.removeEventListener("message", hostListener);
              break;
            }
          }
        };
      }
    }
    window.addEventListener("message", hostListener);
  }

  return (
    <IconButton
      iconSvg='<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path fill-rule="evenodd" clip-rule="evenodd" d="M5 1C3.93913 1 2.92172 1.42143 2.17157 2.17157C1.42143 2.92172 1 3.93913 1 5V19C1 20.0609 1.42143 21.0783 2.17157 21.8284C2.92172 22.5786 3.93913 23 5 23H19C20.0609 23 21.0783 22.5786 21.8284 21.8284C22.5786 21.0783 23 20.0609 23 19V5C23 3.93913 22.5786 2.92172 21.8284 2.17157C21.0783 1.42143 20.0609 1 19 1H5ZM19.53 15.275C19.2418 15.7186 18.8478 16.0836 18.3834 16.337C17.9191 16.5905 17.399 16.7245 16.87 16.727H7.826C7.27575 16.7245 6.73226 16.6056 6.23124 16.3781C5.73022 16.1506 5.28301 15.8196 4.919 15.407L13.299 11.719L19.53 15.275ZM11.947 10.948L4.255 14.333C4.08563 13.9139 3.99903 13.466 4 13.014C4 10.959 5.773 9.307 7.816 9.301L7.881 9.304C8.64464 9.30095 9.39594 9.4967 10.061 9.872L11.947 10.948ZM19.972 14.088L14.722 11.093L14.787 11.065C15.425 10.7954 16.1104 10.656 16.803 10.655L16.869 10.652C18.544 10.652 20 12.005 20 13.689C20 13.825 19.9907 13.9573 19.972 14.088ZM14.294 9.916C14.8678 9.67181 15.4742 9.5128 16.094 9.444C15.715 8.88236 15.2244 8.40486 14.6526 8.04131C14.0809 7.67776 13.4404 7.43596 12.771 7.331C11.4899 7.13643 10.1831 7.44378 9.123 8.189C9.6674 8.30893 10.1908 8.50948 10.676 8.784L10.679 8.786L13.371 10.322L14.287 9.919L14.294 9.916Z" fill="white"/></svg>'
      alt="Add topic"
      size={24}
      onClick={openPicker}
      name="OneDrive"
    />
  );
}
