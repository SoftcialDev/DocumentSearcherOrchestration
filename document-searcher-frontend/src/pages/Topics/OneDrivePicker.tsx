import { v4 as uuid } from "uuid";
import { useMsal } from "@azure/msal-react";
import Button from "../../components/Button";
import IconButton from "../../components/IconButton";

interface PickerProps{
  topicName: string;
  onPicked: () => void;
}


export default function OneDriveFolderPicker({topicName, onPicked}: PickerProps) {
  const { instance, accounts } = useMsal();

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
      const res = await fetch("http://localhost:5000/add-source", {
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
      iconSrc="https://upload.wikimedia.org/wikipedia/commons/3/3c/Microsoft_Office_OneDrive_%282019%E2%80%93present%29.svg"
      alt="Add topic"
      size={24}
      onClick={openPicker}
      name="OneDrive"
    />
  );
}
