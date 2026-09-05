import { computed, ref } from "vue";
import { defineStore } from "pinia";
import { api } from "../api";

export const useAppDataStore = defineStore("app-data", () => {
  const records = ref<Record<string, any>[]>([]);
  const calculated = ref<Record<string, any>[]>([]);
  const monthlyRecords = ref<Record<string, any>[]>([]);
  const dataSource = ref("尚未加载数据");
  const conversionInfo = ref("");
  const busy = ref(false);
  const error = ref("");
  const hasData = computed(() => records.value.length > 0);

  function setData(next: Record<string, any>[], source: string, monthly: Record<string, any>[] = []) {
    records.value = next;
    monthlyRecords.value = monthly;
    calculated.value = [];
    dataSource.value = source;
    error.value = "";
  }

  async function upload(file: File) {
    busy.value = true;
    error.value = "";
    try {
      const form = new FormData();
      form.append("file", file);
      const response = await api.post("/data/upload", form);
      setData(response.data.records || [], `Excel：${response.data.rows} 条记录`);
      conversionInfo.value = response.data.conversion_info || "数据加载成功";
      return response.data;
    } catch (err: any) {
      error.value = err?.response?.data?.detail || "数据加载错误，请检查 Excel 格式或后端服务";
      throw err;
    } finally {
      busy.value = false;
    }
  }

  async function simulate() {
    busy.value = true;
    error.value = "";
    try {
      const response = await api.post("/data/simulate");
      setData(response.data.records || [], `模拟数据：${response.data.records?.length || 0} 条记录`, response.data.monthly_records || []);
      conversionInfo.value = "模拟数据生成完成";
      return response.data;
    } catch (err: any) {
      error.value = err?.response?.data?.detail || "模拟数据生成失败，请检查 FastAPI 服务";
      throw err;
    } finally {
      busy.value = false;
    }
  }

  async function calculate() {
    if (!hasData.value) return [];
    const response = await api.post("/carbon/unit", { records: records.value });
    calculated.value = response.data.records || [];
    return calculated.value;
  }

  return { records, calculated, monthlyRecords, dataSource, conversionInfo, busy, error, hasData, setData, upload, simulate, calculate };
});
