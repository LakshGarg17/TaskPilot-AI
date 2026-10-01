import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";

describe("UI Components & Badge States", () => {
  it("renders badges with proper risk styles", () => {
    const { container: sageContainer } = render(<Badge variant="sage">LOW RISK</Badge>);
    expect(screen.getByText("LOW RISK")).toBeInTheDocument();

    const { container: ochreContainer } = render(<Badge variant="ochre">MEDIUM RISK</Badge>);
    expect(screen.getByText("MEDIUM RISK")).toBeInTheDocument();

    const { container: clayContainer } = render(<Badge variant="clay">HIGH RISK</Badge>);
    expect(screen.getByText("HIGH RISK")).toBeInTheDocument();
  });

  it("renders buttons with click actions", () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Run Task</Button>);
    const btn = screen.getByRole("button", { name: /run task/i });
    expect(btn).toBeInTheDocument();
    fireEvent.click(btn);
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});

describe("Approval Dialog Component", () => {
  it("renders approval modal with sensitive action details and buttons", () => {
    const handleApprove = vi.fn();
    const handleReject = vi.fn();

    render(
      <Dialog open={true}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>TaskPilot Needs Your Approval</DialogTitle>
            <DialogDescription>
              A high-impact action has been planned.
            </DialogDescription>
          </DialogHeader>
          <div data-testid="approval-details">
            <p>TOOL: email_send</p>
            <p>ACTION: Send notification to team@example.com</p>
          </div>
          <DialogFooter>
            <Button variant="secondary" onClick={handleReject}>Reject Action</Button>
            <Button onClick={handleApprove}>Approve & Execute</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    );

    expect(screen.getByText("TaskPilot Needs Your Approval")).toBeInTheDocument();
    expect(screen.getByText("TOOL: email_send")).toBeInTheDocument();
    expect(screen.getByText("ACTION: Send notification to team@example.com")).toBeInTheDocument();

    const approveBtn = screen.getByRole("button", { name: /approve & execute/i });
    const rejectBtn = screen.getByRole("button", { name: /reject action/i });

    fireEvent.click(approveBtn);
    expect(handleApprove).toHaveBeenCalledTimes(1);

    fireEvent.click(rejectBtn);
    expect(handleReject).toHaveBeenCalledTimes(1);
  });
});

describe("Step Timeline & Suggestion Chips", () => {
  it("simulates suggestion chip click filling command box", () => {
    const TestCommandBox = () => {
      const [prompt, setPrompt] = React.useState("");
      const demoChip = "Research the top AI hackathons currently accepting applications";
      return (
        <div>
          <button onClick={() => setPrompt(demoChip)}>Demo Chip</button>
          <textarea
            aria-label="goal-input"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
          />
        </div>
      );
    };

    render(<TestCommandBox />);
    const textarea = screen.getByLabelText("goal-input") as HTMLTextAreaElement;
    expect(textarea.value).toBe("");

    const chip = screen.getByText("Demo Chip");
    fireEvent.click(chip);
    expect(textarea.value).toContain("Research the top AI hackathons");
  });

  it("renders step timeline state representations", () => {
    const steps = [
      { id: "1", title: "web_search", status: "COMPLETED" },
      { id: "2", title: "email_send", status: "WAITING_APPROVAL" },
      { id: "3", title: "calculator", status: "RUNNING" },
    ];

    render(
      <div>
        {steps.map((s) => (
          <div key={s.id} data-testid={`step-${s.id}`}>
            <span>{s.title}</span>
            <Badge variant={s.status === "COMPLETED" ? "sage" : s.status === "WAITING_APPROVAL" ? "clay" : "default"}>
              {s.status}
            </Badge>
          </div>
        ))}
      </div>
    );

    expect(screen.getByText("COMPLETED")).toBeInTheDocument();
    expect(screen.getByText("WAITING_APPROVAL")).toBeInTheDocument();
    expect(screen.getByText("RUNNING")).toBeInTheDocument();
  });
});
