import { defineStore } from "pinia";
import type { LedgerEntry } from "./data";

export const useLedgerEditorStore = defineStore("ledgerEditor", {
  state: () => ({
    visible: false,
    ledger: null as LedgerEntry | null,
  }),
  actions: {
    open(ledger: LedgerEntry) {
      this.ledger = ledger;
      this.visible = true;
    },
    close() {
      this.visible = false;
      this.ledger = null;
    },
  },
});

