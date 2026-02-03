/* SharePointFolderPicker.tsx --------------------------------------- */
import { v4 as uuid } from "uuid";
import { useMsal } from "@azure/msal-react";
import IconButton from "../../components/IconButton";
import { useAuth } from "../../providers/AuthProvider";

interface PickerProps {
  topicName: string;
  onPicked: () => void;
}

export default function SharePointFolderPicker({ topicName, onPicked }: PickerProps) {
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
      site: "Sharepoint",
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

    /* 1. Picker options for SharePoint */
    const pickerOptions = {
      sdk: "8.0",
      entry: {
        sharePoint: {}, // root tenant scopes “More places…”
      },
      authentication: {},
      messaging: { origin: window.location.origin, channelId },
      typesAndSources: { mode: "folders", filters: ["folder"] },
      selection: { mode: "multiple" },
    };

    /* 2. Base URL for SharePoint */
    const tenant = "softcial"; // <- your tenant short name
    const baseUrl = `https://${tenant}.sharepoint.com`;

    const pickerUrl =
      `${baseUrl}/_layouts/15/FilePicker.aspx?` +
      new URLSearchParams({
        filePicker: JSON.stringify(pickerOptions),
        locale: "es-es",
      });

    /* 3. Create popup & POST token */
    const win = window.open(
      "",
      `_picker_${channelId}`,
      "width=1080,height=680"
    );
    if (!win) return;

    const doc = win.document;
    const form = doc.createElement("form");
    form.method = "POST";
    form.action = pickerUrl;

    /* initial token for root SharePoint host */
    const { accessToken } = await instance.acquireTokenSilent({
      account: accounts[0],
      scopes: [`${baseUrl}/.default`], // SharePoint.AllSites.* or MyFiles.*
    });

    const tokenInput = doc.createElement("input");
    tokenInput.type = "hidden";
    tokenInput.name = "access_token";
    tokenInput.value = accessToken;
    form.appendChild(tokenInput);
    doc.body.appendChild(form);
    form.submit();

    /* 4. Message channel handshake */
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
            case "authenticate": {
              const resource = data.resource; // whichever site / host Picker needs
              try {
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
            }

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
        iconSvg='<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path fill-rule="evenodd" clip-rule="evenodd" d="M5 1C3.93913 1 2.92172 1.42143 2.17157 2.17157C1.42143 2.92172 1 3.93913 1 5V19C1 20.0609 1.42143 21.0783 2.17157 21.8284C2.92172 22.5786 3.93913 23 5 23H19C20.0609 23 21.0783 22.5786 21.8284 21.8284C22.5786 21.0783 23 20.0609 23 19V5C23 3.93913 22.5786 2.92172 21.8284 2.17157C21.0783 1.42143 20.0609 1 19 1H5ZM12 6.637H8.355C8.74536 5.73246 9.43022 4.98658 10.2982 4.52063C11.1663 4.05467 12.1664 3.89606 13.136 4.07058C14.1056 4.2451 14.9876 4.74249 15.6387 5.48186C16.2897 6.22124 16.6715 7.15912 16.722 8.143C15.6966 7.99332 14.65 8.16595 13.727 8.637V8.364C13.727 7.41 12.954 6.637 12 6.637ZM4 15.637C4 16.038 4.326 16.364 4.727 16.364H12C12.0956 16.364 12.1902 16.3452 12.2784 16.3086C12.3667 16.272 12.4469 16.2183 12.5144 16.1507C12.5819 16.0831 12.6355 16.0028 12.6719 15.9145C12.7084 15.8262 12.7271 15.7316 12.727 15.636V8.364C12.727 8.26853 12.7082 8.17399 12.6717 8.08579C12.6351 7.99758 12.5816 7.91744 12.5141 7.84993C12.4466 7.78242 12.3664 7.72887 12.2782 7.69234C12.19 7.6558 12.0955 7.637 12 7.637H4.727C4.53443 7.63779 4.34997 7.71464 4.21381 7.85081C4.07764 7.98697 4.00079 8.17143 4 8.364V15.637ZM9.956 9.7C9.499 9.57 8.789 9.443 8.165 9.521C7.852 9.561 7.508 9.658 7.234 9.883C6.938 10.126 6.773 10.478 6.773 10.908C6.773 11.418 7.066 11.764 7.376 11.991C7.67 12.205 8.044 12.36 8.349 12.486L8.354 12.488C8.69 12.628 8.951 12.736 9.136 12.864C9.31 12.984 9.318 13.052 9.318 13.09C9.318 13.33 9.246 13.4 9.203 13.433C9.128 13.488 8.979 13.538 8.715 13.545C8.42556 13.5434 8.13681 13.5166 7.852 13.465L7.525 13.41C7.34105 13.376 7.15633 13.3463 6.971 13.321L6.847 14.314C6.987 14.331 7.138 14.357 7.312 14.388C7.42733 14.4087 7.55433 14.4303 7.693 14.453C8.018 14.505 8.389 14.553 8.74 14.544C9.082 14.536 9.478 14.473 9.798 14.236C10.148 13.977 10.318 13.577 10.318 13.09C10.318 12.583 10.008 12.25 9.705 12.041C9.428 11.851 9.078 11.705 8.786 11.585L8.736 11.565C8.406 11.427 8.146 11.315 7.965 11.182C7.798 11.061 7.773 10.98 7.773 10.908C7.773 10.756 7.82 10.696 7.869 10.656C7.939 10.598 8.072 10.541 8.289 10.513C8.726 10.459 9.289 10.55 9.681 10.662L9.956 9.7ZM9.831 17.363C9.90629 18.1036 10.2626 18.7872 10.8265 19.2732C11.3904 19.7591 12.1192 20.0104 12.8628 19.9755C13.6064 19.9405 14.3083 19.6219 14.8242 19.0851C15.34 18.5484 15.6305 17.8344 15.636 17.09V17.074C15.6329 16.4805 15.4483 15.9021 15.1071 15.4165C14.7659 14.9308 14.2843 14.5612 13.727 14.357V15.635C13.727 16.589 12.954 17.363 12 17.363H9.831ZM20 13.09C19.9994 12.3607 19.7995 11.6454 19.4218 11.0215C19.0442 10.3976 18.5032 9.88881 17.8573 9.55008C17.2115 9.21134 16.4853 9.05558 15.7573 9.09963C15.0294 9.14368 14.3273 9.38586 13.727 9.8V13.312C14.5529 13.5304 15.2846 14.0134 15.8101 14.687C16.3356 15.3606 16.6261 16.1877 16.637 17.042C17.5755 16.8898 18.4292 16.4086 19.0454 15.6845C19.6615 14.9605 19.9999 14.0408 20 13.09Z" fill="white"/></svg>'
        size={24}
        onClick={openPicker}
        name="Sharepoint"
      />
  );
}
