
import { apiRequest, jsonRequest } from "@ofs/shared/api";

export type DeliveryPauseStatus = {
    paused: boolean;
};

export async function getDeliveryPause() {
    return apiRequest<DeliveryPauseStatus>(
        "/api/settings/delivery-pause"
    );
}

export async function setDeliveryPause(paused: boolean) {
    return apiRequest<DeliveryPauseStatus>(
        "/api/settings/delivery-pause",
        jsonRequest("PUT", { paused })
    );
}
