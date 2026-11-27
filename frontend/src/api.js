// Appels à l'API et gestion centralisée des erreurs.
//
// Le backend renvoie toutes ses erreurs au format :
//   { "erreur": { "code": "...", "message": "...", "details": {...} } }
// appelerApi les transforme en ErreurApi : le code sert à réagir à un cas
// précis (ex : 'CARTE_NON_CHARGEE'), le message s'affiche tel quel.

export const API = 'http://localhost:8080/api';

export class ErreurApi extends Error {
  constructor(code, message, details = {}) {
    super(message);
    this.code = code;
    this.details = details;
  }
}

// fetch + vérification de la réponse. Renvoie le JSON, ou lance une ErreurApi.
export async function appelerApi(url, options = {}) {
  let response;
  try {
    response = await fetch(url, options);
  } catch {
    throw new ErreurApi('RESEAU', "Impossible de contacter l'API (backend démarré ?)");
  }

  // .catch : une réponse sans corps JSON ne doit pas masquer le statut HTTP.
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const e = data?.erreur;
    throw new ErreurApi(
      e?.code ?? 'INCONNUE',
      e?.message ?? `Erreur ${response.status}`,
      e?.details
    );
  }
  return data;
}
