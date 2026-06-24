import { PORT1 } from "@/api/config/servicePort";
import http from "@/api";

export interface WorkbenchTodoItem {
  key: string;
  title: string;
  description: string;
  count: number;
  path: string;
  query?: Record<string, string>;
}

export interface WorkbenchTodoData {
  items: WorkbenchTodoItem[];
  total: number;
}

export const getWorkbenchTodos = () => {
  return http.get<WorkbenchTodoData>(PORT1 + `/biz/home/todos`, {}, { loading: false });
};
