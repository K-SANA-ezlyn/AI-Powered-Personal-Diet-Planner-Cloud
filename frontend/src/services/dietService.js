import client from "../api/client";

/**
 * services/dietService.js — profile, plan generation, saved plans, files.
 */
export const profileService = {
  get: () => client.get("/profile").then((r) => r.data),
  save: (payload) => client.put("/profile", payload).then((r) => r.data),
};

export const dietService = {
  generate: (overrides = {}) =>
    client.post("/diet/generate-plan", overrides).then((r) => r.data),
};

export const planService = {
  list: () => client.get("/plans").then((r) => r.data),
  get: (id) => client.get(`/plans/${id}`).then((r) => r.data),
  save: (plan, title = null) =>
    client.post("/plans", { plan, title }).then((r) => r.data),
  delete: (id) => client.delete(`/plans/${id}`).then((r) => r.data),
};

export const fileService = {
  list: () => client.get("/files").then((r) => r.data),
  upload: (file, onProgress) => {
    const form = new FormData();
    form.append("file", file);
    return client
      .post("/files/upload", form, {
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress: onProgress,
      })
      .then((r) => r.data);
  },
  downloadUrl: (id) =>
    `${import.meta.env.VITE_API_BASE || "/api"}/files/${id}/download`,
  delete: (id) => client.delete(`/files/${id}`).then((r) => r.data),
};

export const dashboardService = {
  get: () => client.get("/dashboard").then((r) => r.data),
};
