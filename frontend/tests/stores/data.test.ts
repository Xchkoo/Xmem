import { beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";

vi.mock("../../src/api/client", () => {
  return {
    default: {
      get: vi.fn(),
      post: vi.fn(),
      patch: vi.fn(),
      delete: vi.fn(),
      defaults: { baseURL: "/api" },
    },
  };
});

/**
 * 构造一个最小的 LedgerEntry 用于 data store 测试。
 */
const createLedger = (overrides: any = {}) => {
  return {
    id: 1,
    raw_text: "午餐 10 元",
    currency: "CNY",
    status: "completed",
    created_at: "2026-01-10T06:30:00Z",
    updated_at: null,
    ...overrides,
  };
};

describe("useDataStore", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
    vi.spyOn(console, "log").mockImplementation(() => {});
    vi.spyOn(console, "error").mockImplementation(() => {});
  });

  it("fetchLedgers 会更新列表与分页信息", async () => {
    const api = (await import("../../src/api/client")).default as any;
    api.get.mockResolvedValue({
      data: {
        items: [createLedger({ id: 1 }), createLedger({ id: 2 })],
        page: 1,
        page_size: 20,
        total: 2,
        total_pages: 1,
      },
    });

    const { useDataStore } = await import("../../src/stores/data");
    const data = useDataStore();

    const result = await data.fetchLedgers(undefined, 1, 20);

    expect(result.total).toBe(2);
    expect(data.ledgers).toHaveLength(2);
    expect(data.ledgerPagination.totalPages).toBe(1);
    expect(api.get).toHaveBeenCalledWith("/ledger", { params: { page: 1, page_size: 20 } });
  });

  it("updateLedger 会替换 store 中对应的 ledger", async () => {
    const api = (await import("../../src/api/client")).default as any;
    api.patch.mockResolvedValue({ data: createLedger({ id: 1, amount: 88.8 }) });

    const { useDataStore } = await import("../../src/stores/data");
    const data = useDataStore();
    data.ledgers = [createLedger({ id: 1, amount: 10 }), createLedger({ id: 2, amount: 20 })];

    await data.updateLedger(1, { amount: 88.8 });

    expect(data.ledgers.find((l) => l.id === 1)?.amount).toBe(88.8);
    expect(api.patch).toHaveBeenCalledWith("/ledger/1", { amount: 88.8 });
  });

  it("reset 会清空内存缓存与分页信息", async () => {
    const { useDataStore } = await import("../../src/stores/data");
    const data = useDataStore();
    data.ledgers = [createLedger()];
    data.notes = [{ id: 1, body_md: "x", created_at: "2026-01-01T00:00:00Z" }];
    data.todos = [{ id: 1, title: "t", completed: false, created_at: "2026-01-01T00:00:00Z" }];
    data.ledgerPagination.totalPages = 9;

    data.reset();

    expect(data.ledgers).toHaveLength(0);
    expect(data.notes).toHaveLength(0);
    expect(data.todos).toHaveLength(0);
    expect(data.ledgerPagination.totalPages).toBe(0);
  });
});

