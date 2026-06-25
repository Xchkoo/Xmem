package com.xmem.android.ui.navigation

sealed class Screen(val route: String) {
    object Login : Screen("login")
    object Register : Screen("register")
    object Home : Screen("home")
    object Notes : Screen("notes")
    object NoteDetail : Screen("note/{noteId}") {
        fun createRoute(noteId: Int) = "note/$noteId"
    }
    object NoteEditor : Screen("editor/{noteId}") {
        fun createRoute(noteId: Int?) = "editor/${noteId ?: -1}"
    }
    object Ledgers : Screen("ledgers")
    object LedgerDetail : Screen("ledger/{ledgerId}") {
        fun createRoute(ledgerId: Int) = "ledger/$ledgerId"
    }
    object Statistics : Screen("statistics")
    object Todos : Screen("todos")
    object Settings : Screen("settings")
}
