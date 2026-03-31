"use client";

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

export default function Pagination({
  currentPage,
  totalPages,
  onPageChange,
}: PaginationProps) {
  const maxVisible = 7;
  let startP = Math.max(1, currentPage - 3);
  let endP = Math.min(totalPages, startP + maxVisible - 1);
  if (endP - startP < maxVisible - 1) {
    startP = Math.max(1, endP - maxVisible + 1);
  }

  const pages: (number | "ellipsis-start" | "ellipsis-end")[] = [];

  if (startP > 1) {
    pages.push(1);
    if (startP > 2) pages.push("ellipsis-start");
  }
  for (let i = startP; i <= endP; i++) {
    pages.push(i);
  }
  if (endP < totalPages) {
    if (endP < totalPages - 1) pages.push("ellipsis-end");
    pages.push(totalPages);
  }

  const btnBase =
    "min-w-[40px] h-10 px-3 border border-surface-border bg-white rounded-md text-sm transition-all hover:border-primary hover:text-primary";
  const btnActive = "!bg-primary !text-white !border-primary";
  const btnDisabled = "opacity-40 !cursor-default hover:border-surface-border hover:text-inherit";

  return (
    <div className="flex justify-center gap-1.5 mt-6">
      <button
        className={`${btnBase} ${currentPage === 1 ? btnDisabled : "cursor-pointer"}`}
        disabled={currentPage === 1}
        onClick={() => onPageChange(currentPage - 1)}
      >
        &laquo;
      </button>

      {pages.map((p, idx) => {
        if (typeof p === "string") {
          return (
            <button key={p + idx} className={`${btnBase} ${btnDisabled}`} disabled>
              ...
            </button>
          );
        }
        return (
          <button
            key={p}
            className={`${btnBase} cursor-pointer ${p === currentPage ? btnActive : ""}`}
            onClick={() => onPageChange(p)}
          >
            {p}
          </button>
        );
      })}

      <button
        className={`${btnBase} ${currentPage === totalPages ? btnDisabled : "cursor-pointer"}`}
        disabled={currentPage === totalPages}
        onClick={() => onPageChange(currentPage + 1)}
      >
        &raquo;
      </button>
    </div>
  );
}
