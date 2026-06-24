<template>
  <div class="table-box workbench-todo-page" v-loading="loading">
    <el-empty v-if="!loading && !items.length" description="暂无待办事项" />
    <el-row v-else :gutter="16">
      <el-col v-for="item in items" :key="item.key" :xs="24" :sm="12" :lg="8">
        <el-card shadow="hover" class="todo-card" @click="goTodo(item)">
          <div class="todo-card__head">
            <span class="todo-card__title">{{ item.title }}</span>
            <el-badge :value="item.count" :max="99" type="danger" />
          </div>
          <p class="todo-card__desc">{{ item.description }}</p>
          <el-button type="primary" link>去处理</el-button>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts" name="workbenchTodo">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { getWorkbenchTodos, type WorkbenchTodoItem } from "@/api/modules/bizHome";

const router = useRouter();
const loading = ref(false);
const items = ref<WorkbenchTodoItem[]>([]);

const fetchTodos = async () => {
  loading.value = true;
  try {
    const res = await getWorkbenchTodos();
    items.value = res.data?.items || [];
  } finally {
    loading.value = false;
  }
};

const goTodo = (item: WorkbenchTodoItem) => {
  router.push({
    path: item.path,
    query: item.query || {}
  });
};

onMounted(fetchTodos);
</script>

<style scoped lang="scss">
.workbench-todo-page {
  padding: 8px 4px;

  .todo-card {
    margin-bottom: 16px;
    cursor: pointer;
    transition: transform 0.15s ease;

    &:hover {
      transform: translateY(-2px);
    }

    &__head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 8px;
    }

    &__title {
      font-size: 16px;
      font-weight: 600;
      color: var(--el-text-color-primary);
    }

    &__desc {
      margin: 0 0 8px;
      min-height: 40px;
      font-size: 13px;
      color: var(--el-text-color-secondary);
      line-height: 1.5;
    }
  }
}
</style>
