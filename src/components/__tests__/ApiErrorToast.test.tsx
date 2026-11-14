import { act, fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import ApiErrorToast from "../ApiErrorToast";
import { API_DISCONNECTED_EVENT, API_RECONNECTED_EVENT } from "@/lib/api";

describe("ApiErrorToast", () => {
  it("announces connection loss and clears after recovery or dismissal", () => {
    render(<ApiErrorToast />);
    act(() => {
      window.dispatchEvent(
        new CustomEvent(API_DISCONNECTED_EVENT, {
          detail: { status: 0, detail: "Network request failed." },
        }),
      );
    });

    expect(screen.getByRole("alert")).toHaveTextContent("API connection lost");
    expect(screen.getByRole("alert")).toHaveTextContent("Network request failed.");

    fireEvent.click(screen.getByRole("button", { name: "Dismiss API connection alert" }));
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();

    act(() => {
      window.dispatchEvent(
        new CustomEvent(API_DISCONNECTED_EVENT, {
          detail: { status: 0, detail: "Connection lost again." },
        }),
      );
      window.dispatchEvent(new Event(API_RECONNECTED_EVENT));
    });
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });
});
