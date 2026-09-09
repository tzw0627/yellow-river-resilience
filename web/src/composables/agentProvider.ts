import { computed, ref } from "vue";
import { getAgentStatus, type AgentProviderOption, type AgentStatus } from "../services/api";

const status = ref<AgentStatus | null>(null);
const selectedProvider = ref("openai");
let loadingPromise: Promise<void> | null = null;

const fallbackProviders: AgentProviderOption[] = [
  {
    id: "openai",
    label: "GPT / OpenAI",
    configured: false,
    model: "gpt-4o-mini",
    base_url: "",
  },
  {
    id: "mimo",
    label: "小米 MiMo",
    configured: false,
    model: "mimo-v2.5-pro",
    base_url: "https://api.xiaomimimo.com/v1",
  },
];

const providerOptions = computed<AgentProviderOption[]>(
  () => status.value?.providers ?? fallbackProviders,
);

const selectedProviderMeta = computed(() =>
  providerOptions.value.find((provider) => provider.id === selectedProvider.value),
);

const selectedProviderConfigured = computed(
  () => selectedProviderMeta.value?.configured ?? false,
);

const selectedProviderModel = computed(
  () => selectedProviderMeta.value?.model ?? "-",
);

async function loadAgentProviderStatus() {
  if (status.value || loadingPromise) return loadingPromise;
  loadingPromise = (async () => {
    try {
      status.value = await getAgentStatus();
      selectedProvider.value =
        status.value.provider ??
        status.value.providers?.find((provider) => provider.configured)?.id ??
        "openai";
    } catch {
      // Keep the provider buttons available and let the panel show its offline state.
    } finally {
      loadingPromise = null;
    }
  })();
  return loadingPromise;
}

function selectProvider(provider: string) {
  if (providerOptions.value.some((option) => option.id === provider)) {
    selectedProvider.value = provider;
  }
}

export function useAgentProvider() {
  return {
    status,
    selectedProvider,
    providerOptions,
    selectedProviderConfigured,
    selectedProviderModel,
    loadAgentProviderStatus,
    selectProvider,
  };
}
