import type { ReactNode } from "react";

export function FieldDescription({
  id,
  children,
}: {
  id: string;
  children: ReactNode;
}) {
  return (
    <p id={id} className="text-xs leading-relaxed text-muted-foreground">
      {children}
    </p>
  );
}
