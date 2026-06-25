package com.xmem.android.ui.todos

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.PushPin
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.style.TextDecoration
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.xmem.android.data.model.Todo
import com.xmem.android.ui.common.UiState

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun TodosScreen(
    viewModel: TodosViewModel = hiltViewModel()
) {
    var newTodoTitle by remember { mutableStateOf("") }
    val state by viewModel.state.collectAsState()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("待办清单", fontWeight = FontWeight.Bold) }
            )
        }
    ) { innerPadding ->
        Column(modifier = Modifier.padding(innerPadding)) {
            // Add Todo Input
            OutlinedTextField(
                value = newTodoTitle,
                onValueChange = { newTodoTitle = it },
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(16.dp),
                placeholder = { Text("添加新待办...") },
                trailingIcon = {
                    IconButton(onClick = {
                        if (newTodoTitle.isNotBlank()) {
                            viewModel.addTodo(newTodoTitle)
                            newTodoTitle = ""
                        }
                    }) {
                        Icon(Icons.Default.Add, contentDescription = "添加")
                    }
                },
                keyboardOptions = KeyboardOptions(imeAction = ImeAction.Done),
                keyboardActions = KeyboardActions(onDone = {
                    if (newTodoTitle.isNotBlank()) {
                        viewModel.addTodo(newTodoTitle)
                        newTodoTitle = ""
                    }
                }),
                shape = MaterialTheme.shapes.medium
            )

            when (state) {
                is UiState.Loading -> {
                    Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                        CircularProgressIndicator()
                    }
                }
                is UiState.Success -> {
                    val todos = (state as UiState.Success<List<Todo>>).data
                    LazyColumn(
                        modifier = Modifier.fillMaxSize(),
                        contentPadding = PaddingValues(bottom = 16.dp)
                    ) {
                        items(todos) { todo ->
                            TodoItemRow(
                                todo = todo,
                                onToggle = { viewModel.toggleTodo(todo.id) },
                                onDelete = { viewModel.deleteTodo(todo.id) }
                            )
                            
                            // Sub-items if any
                            todo.group_items?.forEach { subTodo ->
                                TodoItemRow(
                                    todo = subTodo,
                                    onToggle = { viewModel.toggleTodo(subTodo.id) },
                                    onDelete = { viewModel.deleteTodo(subTodo.id) },
                                    isSubItem = true
                                )
                            }
                        }
                    }
                }
                is UiState.Error -> {
                    Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                        Text((state as UiState.Error).message, color = MaterialTheme.colorScheme.error)
                    }
                }
                else -> {}
            }
        }
    }
}

@Composable
fun TodoItemRow(
    todo: Todo,
    onToggle: () -> Unit,
    onDelete: () -> Unit,
    isSubItem: Boolean = false
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(start = if (isSubItem) 48.dp else 16.dp, end = 16.dp, top = 8.dp, bottom = 8.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Checkbox(
            checked = todo.completed,
            onCheckedChange = { onToggle() }
        )
        Spacer(modifier = Modifier.width(8.dp))
        Text(
            text = todo.title,
            style = MaterialTheme.typography.bodyLarge,
            textDecoration = if (todo.completed) TextDecoration.LineThrough else TextDecoration.None,
            color = if (todo.completed) MaterialTheme.colorScheme.onSurfaceVariant else MaterialTheme.colorScheme.onSurface,
            modifier = Modifier.weight(1)
        )
        if (todo.is_pinned == true && !isSubItem) {
            Icon(
                Icons.Default.PushPin,
                contentDescription = "置顶",
                tint = MaterialTheme.colorScheme.primary,
                modifier = Modifier.size(16.dp)
            )
        }
        IconButton(onClick = onDelete) {
            Icon(
                Icons.Default.Delete,
                contentDescription = "删除",
                tint = MaterialTheme.colorScheme.error.copy(alpha = 0.6f),
                modifier = Modifier.size(20.dp)
            )
        }
    }
}
