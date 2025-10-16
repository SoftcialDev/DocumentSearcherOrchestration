import { createRemoteJWKSet, jwtVerify, decodeJwt, JWTPayload } from "jose";

const ISSUER = "https://softcial.com/"; // must match your server 'iss'
const JWKS = createRemoteJWKSet(new URL("http://localhost:8000/client/pubkey"));

export async function verifyLicenseJWT(token: string) {
  const { payload } = await jwtVerify(token, JWKS, {
    algorithms: ["RS256"],
    issuer: ISSUER,
    clockTolerance: 5, // seconds of skew
  });
  return payload; // JWTPayload (contains your custom claims too)
}

export function secondsLeft(token: string) {
  const p = decodeJwt(token);
  const now = Math.floor(Date.now() / 1000);
  return (p.exp ?? 0) - now;
}