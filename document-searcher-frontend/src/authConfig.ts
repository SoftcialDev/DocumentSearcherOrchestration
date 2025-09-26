export const msalConfig = {
  auth: {
    clientId: "d8c01861-4bc1-45bc-8778-23691418878d",
    authority: `https://login.microsoftonline.com/a080ad22-43aa-4696-b40b-9b68b702c9f3`, // change if hosted elsewhere
  },
  cache: {
    cacheLocation: "sessionStorage",
    storeAuthStateInCookie: false,
  },
};

export const loginRequest = {
  scopes: [
    "Files.ReadWrite.All",
    "Sites.ReadWrite.All",
    "offline_access"
  ]
};
