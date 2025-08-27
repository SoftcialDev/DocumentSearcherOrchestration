import { v4 as uuid } from "uuid";
import { useMsal } from "@azure/msal-react";
import Button from "../Button";

export default function FolderPicker() {
  const { instance, accounts } = useMsal();

  async function openPicker() {
    const channelId = uuid();
    const pickerOptions = {
      sdk: "8.0",
      messaging: { origin: window.location.origin, channelId },
      authentication: {},
      entry: { sharePoint: {} }, // Corregido: era tokensentry
      typesAndSources: {
        mode: "folders",
        filters: ["folder"],
      },
      selection: { mode: "multiple" },
    };

    const baseUrl = "https://softcial.sharepoint.com";
    const pickerUrl =
      `${baseUrl}/_layouts/15/FilePicker.aspx?` +
      new URLSearchParams({
        filePicker: JSON.stringify(pickerOptions),
        locale: "es-es",
      });

    const win = window.open(
      "",
      `_picker_${channelId}`,
      "width=1080,height=680"
    );
    const doc = win!.document;
    const form = doc.createElement("form");
    form.method = "POST";
    form.action = pickerUrl;

    // token inicial (sitio base)
    const tokenResp = await instance.acquireTokenSilent({
      account: accounts[0],
      scopes: [`${baseUrl}/.default`],
    });

    const tokenInput = doc.createElement("input");
    tokenInput.type = "hidden";
    tokenInput.name = "access_token";
    tokenInput.value = tokenResp.accessToken;
    form.appendChild(tokenInput);

    doc.body.appendChild(form);
    form.submit();

    function hostListener(evt: MessageEvent) {
      if (evt.source !== win) return;
      const msg = evt.data;

      if (
        msg.type === "initialize" &&
        msg.channelId === pickerOptions.messaging.channelId
      ) {
        const port: MessagePort = evt.ports[0];
        port.start();
        port.postMessage({ type: "activate" });

        port.onmessage = async (e) => {
          const { id, type, data } = e.data;
          if (type !== "command") return;
          port.postMessage({ type: "acknowledge", id });

          switch (data.command) {
            case "authenticate": {
              const resource = data.resource || baseUrl;
              try {
                const tokenForResource = await instance.acquireTokenSilent({
                  account: accounts[0],
                  scopes: [`${resource}/.default`],
                });

                port.postMessage({
                  type: "result",
                  id,
                  data: {
                    result: "token",
                    token: tokenForResource.accessToken,
                  },
                });
              } catch (err) {
                console.error("Error obteniendo token:", err);
              }
              break;
            }

            case "pick": {
                // ← the command object
                const payload = data;

                // v8 spec: always `items` (array). Fall‑back aliases for safety.
                const selected = payload.items
                                ?? payload.value
                                ?? payload.driveItems
                                ?? [];

                if (!Array.isArray(selected) || selected.length === 0) {
                    console.warn("Picker returned no selections", payload);
                    port.postMessage({ type: "result", id, data: { result: "cancel" } });
                    break;
                }

                // 👉 display or store the metadata you want
                selected.forEach((item: any) => {
                    console.table({
                    name:    item.name,
                    webUrl:  item.webUrl,
                    id:      item.id,
                    driveId: item.parentReference?.driveId,
                    size:    item.size,
                    lastMod: item.lastModifiedDateTime
                    });
                });

                // return success so the picker closes its UI nicely
                port.postMessage({ type: "result", id, data: { result: "success" } });

                // close popup & detach listener
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
    <Button
      onClick={openPicker}
      text={"Seleccionar carpetas"}
      type={"ACCEPT"}
      icon="none"
    />
  );
}
