/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

// external imports
import { fileTypeFromBuffer } from "file-type";
// plane imports
import type { TFileMetaDataLite, TFileSignedURLResponse } from "@plane/types";
import { DANGEROUS_EXTENSIONS } from "@plane/constants";

/**
 * @description Filename validation - checks for double extensions and dangerous patterns
 * @param {string} filename
 * @returns {string | null} Error message if invalid, null if valid
 */
const validateFilename = (filename: string): string | null => {
  if (!filename || filename.trim().length === 0) {
    return "Filename cannot be empty";
  }

  // Check for dot files (e.g., .htaccess, .env)
  if (filename.startsWith(".")) {
    return "Hidden files (starting with dot) are not allowed";
  }

  // Check for path separators
  if (filename.includes("/") || filename.includes("\\")) {
    return "Filename cannot contain path separators";
  }

  const parts = filename.split(".");

  // Check for double extensions with dangerous patterns
  if (parts.length >= 3) {
    const secondLastExt = parts[parts.length - 2]?.toLowerCase() || "";
    if (DANGEROUS_EXTENSIONS.includes(secondLastExt)) {
      return "File has suspicious double extension";
    }
  }

  // Check if the actual extension is dangerous
  const extension = parts[parts.length - 1]?.toLowerCase() || "";
  if (DANGEROUS_EXTENSIONS.includes(extension)) {
    return `File extension '${extension}' is not allowed`;
  }

  return null;
};

/**
 * @description from the provided signed URL response, generate a payload to be used to upload the file
 * @param {TFileSignedURLResponse} signedURLResponse
 * @param {File} file
 * @returns {FormData} file upload request payload
 */
export const generateFileUploadPayload = (signedURLResponse: TFileSignedURLResponse, file: File): FormData => {
  const formData = new FormData();
  Object.entries(signedURLResponse.upload_data.fields).forEach(([key, value]) => formData.append(key, value));
  formData.append("file", file);
  return formData;
};

/**
 * @description Detect MIME type from file signature using file-type library
 * @param {File} file
 * @returns {Promise<string>} detected MIME type or empty string if unknown
 */
const detectMimeTypeFromSignature = async (file: File): Promise<string> => {
  try {
    // Read first 4KB which is usually sufficient for most file type detection
    const chunk = file.slice(0, 4096);
    const buffer = await chunk.arrayBuffer();
    const uint8Array = new Uint8Array(buffer);

    const fileType = await fileTypeFromBuffer(uint8Array);
    return fileType?.mime || "";
  } catch (_error) {
    return "";
  }
};

/**
 * @description Validate and detect the MIME type of a file using signature detection
 * Also performs basic security checks on filename
 * @param {File} file
 * @returns {Promise<string>} validated and detected MIME type
 */
// Karya: text formats (CSV/TXT) have no signature and legacy Office files sniff as the generic OLE container,
// which made Excel/CSV attachments fail (5 Oct 2026). Fall back to the extension, then the browser's type.
// The server re-checks everything against its allowlist (apps/api/plane/karya/files.py).
const KARYA_GENERIC_TYPES = new Set(["", "application/octet-stream", "application/x-cfb", "application/zip", "text/plain"]);
const KARYA_EXTENSION_TYPES: Record<string, string> = {
  csv: "text/csv",
  tsv: "text/plain",
  txt: "text/plain",
  md: "text/markdown",
  xls: "application/vnd.ms-excel",
  xlsx: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  xlsm: "application/vnd.ms-excel.sheet.macroEnabled.12",
  xlsb: "application/vnd.ms-excel.sheet.binary.macroEnabled.12",
  doc: "application/msword",
  docx: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  ppt: "application/vnd.ms-powerpoint",
  pptx: "application/vnd.openxmlformats-officedocument.presentationml.presentation",
  ods: "application/vnd.oasis.opendocument.spreadsheet",
  odt: "application/vnd.oasis.opendocument.text",
  json: "application/json",
  heic: "image/heic",
  heif: "image/heif",
  mov: "video/quicktime",
  m4v: "video/x-m4v",
  "3gp": "video/3gpp",
  mkv: "video/x-matroska",
};
const karyaTypeFromName = (name: string): string =>
  KARYA_EXTENSION_TYPES[name.split(".").pop()?.toLowerCase() ?? ""] ?? "";

const validateAndDetectFileType = async (file: File): Promise<string> => {
  // Basic filename validation
  const filenameError = validateFilename(file.name);
  if (filenameError) {
    console.warn(`File validation warning: ${filenameError}`);
  }

  try {
    const signatureType = await detectMimeTypeFromSignature(file);
    if (signatureType && !KARYA_GENERIC_TYPES.has(signatureType)) {
      return signatureType;
    }
    // Karya: generic or unknown signature — prefer what the name says, then what the browser says
    const byName = karyaTypeFromName(file.name);
    if (byName) return byName;
    if (signatureType) return signatureType;
    if (file.type) return file.type;
  } catch (_error) {
    console.warn("Error detecting file type from signature:", _error);
  }

  // fallback for unknown files
  return "";
};

/**
 * @description returns the necessary file meta data to upload a file
 * @param {File} file
 * @returns {Promise<TFileMetaDataLite>} payload with file info
 */
export const getFileMetaDataForUpload = async (file: File): Promise<TFileMetaDataLite> => {
  const fileType = await validateAndDetectFileType(file);
  return {
    name: file.name,
    size: file.size,
    type: fileType,
  };
};

/**
 * @description this function returns the assetId from the asset source
 * @param {string} src
 * @returns {string} assetId
 */
export const getAssetIdFromUrl = (src: string): string => {
  const sourcePaths = src.split("/");
  const assetUrl = sourcePaths[sourcePaths.length - 1];
  return assetUrl ?? "";
};
