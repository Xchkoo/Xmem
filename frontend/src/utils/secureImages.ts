import api from "../api/client";

/**
 * Finds all images in the container that are protected (e.g. start with /notes/files/)
 * and fetches them with authentication headers, replacing the src with a blob URL.
 */
export const replaceImagesWithSecureUrls = async (container: HTMLElement) => {
  if (!container) return;

  const images = container.querySelectorAll("img");
  
  images.forEach(async (img) => {
    const src = img.getAttribute("src");
    // Only process relative paths starting with /notes/files/
    // We assume markdown generates relative paths like /notes/files/...
    if (src && src.startsWith("/notes/files/") && !src.startsWith("blob:")) {
      try {
        // Check if we already have a loading flag to avoid double fetch
        if (img.dataset.loading === "true") return;
        img.dataset.loading = "true";

        // Fetch with auth headers
        // api.get uses baseURL (usually /api), so /notes/files/... becomes /api/notes/files/...
        const response = await api.get(src, { responseType: "blob" });
        const blobUrl = URL.createObjectURL(response.data);
        
        img.src = blobUrl;
        img.dataset.loaded = "true";
      } catch (error) {
        console.error("Failed to load secure image:", src, error);
        // Set error style or placeholder
        img.style.opacity = "0.5";
        img.style.border = "1px solid red";
      } finally {
        img.dataset.loading = "false";
      }
    }
  });
};
