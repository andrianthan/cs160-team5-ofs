
import { apiRequest, jsonRequest } from "@ofs/shared/api";

export async function cancelOrderOverride(
    orderId: number,
    reason: string
) {
    return apiRequest(
        `/api/orders/${orderId}/override`,
        jsonRequest("POST", {
            action: "cancel",
            reason,
            confirmed: true,
        })
    );
}
