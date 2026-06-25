package com.xmem.android.ui.main

import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Assignment
import androidx.compose.material.icons.filled.Book
import androidx.compose.material.icons.filled.Checklist
import androidx.compose.material.icons.filled.AutoAwesome
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.navigation.NavDestination.Companion.hierarchy
import androidx.navigation.NavGraph.Companion.findStartDestination
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.xmem.android.ui.ai.AiAssistantPanel
import com.xmem.android.ui.ledgers.LedgersScreen
import com.xmem.android.ui.navigation.Screen
import com.xmem.android.ui.notes.NotesScreen
import com.xmem.android.ui.settings.SettingsScreen
import com.xmem.android.ui.todos.TodosScreen

@Composable
fun MainContainer(
    onLogout: () -> Unit,
    onNoteClick: (Long) -> Unit,
    onAddNote: () -> Unit,
    onStatisticsClick: () -> Unit
) {
    val navController = rememberNavController()
    var showAiPanel by remember { mutableStateOf(false) }

    val items = listOf(
        NavigationItem("笔记", Screen.Notes.route, Icons.Filled.Book),
        NavigationItem("账本", Screen.Ledgers.route, Icons.Filled.Assignment),
        NavigationItem("待办", Screen.Todos.route, Icons.Filled.Checklist),
        NavigationItem("设置", Screen.Settings.route, Icons.Filled.Settings)
    )

    Scaffold(
        floatingActionButton = {
            val navBackStackEntry by navController.currentBackStackEntryAsState()
            val currentRoute = navBackStackEntry?.destination?.route
            // Only show AI FAB on main list screens
            if (currentRoute in listOf(Screen.Notes.route, Screen.Ledgers.route, Screen.Todos.route)) {
                FloatingActionButton(
                    onClick = { showAiPanel = true },
                    containerColor = MaterialTheme.colorScheme.primaryContainer,
                    contentColor = MaterialTheme.colorScheme.onPrimaryContainer
                ) {
                    Icon(Icons.Default.AutoAwesome, contentDescription = "AI 助手")
                }
            }
        },
        bottomBar = {
            NavigationBar(
                containerColor = MaterialTheme.colorScheme.surface,
                contentColor = MaterialTheme.colorScheme.onSurface
            ) {
                val navBackStackEntry by navController.currentBackStackEntryAsState()
                val currentDestination = navBackStackEntry?.destination
                items.forEach { item ->
                    NavigationBarItem(
                        icon = { Icon(item.icon, contentDescription = item.label) },
                        label = { Text(item.label) },
                        selected = currentDestination?.hierarchy?.any { it.route == item.route } == true,
                        onClick = {
                            navController.navigate(item.route) {
                                popUpTo(navController.graph.findStartDestination().id) {
                                    saveState = true
                                }
                                launchSingleTop = true
                                restoreState = true
                            }
                        }
                    )
                }
            }
        }
    ) { innerPadding ->
        NavHost(
            navController = navController,
            startDestination = Screen.Notes.route,
            modifier = Modifier.padding(innerPadding)
        ) {
            composable(Screen.Notes.route) {
                NotesScreen(
                    onNoteClick = onNoteClick,
                    onAddNote = onAddNote
                )
            }
            composable(Screen.Ledgers.route) {
                LedgersScreen(
                    onStatisticsClick = onStatisticsClick,
                    onLedgerClick = { ledgerId ->
                        // navController.navigate(Screen.LedgerDetail.createRoute(ledgerId.toInt()))
                    }
                )
            }
            composable(Screen.Todos.route) {
                TodosScreen()
            }
            composable(Screen.Settings.route) {
                SettingsScreen(
                    onLogout = onLogout
                )
            }
        }

        if (showAiPanel) {
            AiAssistantPanel(onClose = { showAiPanel = false })
        }
    }
}

data class NavigationItem(val label: String, val route: String, val icon: androidx.compose.ui.graphics.vector.ImageVector)
