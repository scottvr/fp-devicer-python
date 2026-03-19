from .core.adapter_factory import (
	AdapterFactory,
	AdapterFactoryOptions,
	createInMemoryAdapter,
	createPostgresAdapter,
	createRedisAdapter,
	createSqliteAdapter,
)
from .core.manager import DeviceManager, IdentifyResult
from .libs.adapters import (
	InMemoryAdapter,
	PostgresAdapter,
	RedisAdapter,
	SqliteAdapter,
	create_in_memory_adapter,
	create_postgres_adapter,
	create_redis_adapter,
	create_sqlite_adapter,
)
from .libs.confidence import (
	DEFAULT_WEIGHTS,
	ConfidenceBreakdown,
	FamilyScore,
	calculate_confidence,
	calculate_confidence_breakdown,
	calculate_confidence_profile,
	create_confidence_calculator,
)
from .libs.default_observability import DefaultMetrics, default_logger, default_metrics
from .libs.default_plugins import initialize_default_registry
from .libs.hashing import canonicalized_stringify, compare_hashes, get_hash, get_hash_difference, get_tlsh_hash
from .libs.registry import (
	clear_registry,
	get_global_registry,
	register_comparator,
	register_plugin,
	register_weight,
	set_default_weight,
	unregister_comparator,
	unregister_weight,
)
from .types import (
	Comparator,
	ComparisonOptions,
	DeviceMatch,
	FPDataSet,
	FPUserDataSet,
	Logger,
	Metrics,
	ObservabilityOptions,
	StorageAdapter,
	StoredFingerprint,
)

__all__ = [
	"AdapterFactory",
	"AdapterFactoryOptions",
	"Comparator",
	"ComparisonOptions",
	"DEFAULT_WEIGHTS",
	"ConfidenceBreakdown",
	"DeviceManager",
	"IdentifyResult",
	"DeviceMatch",
	"FPDataSet",
	"FPUserDataSet",
	"InMemoryAdapter",
	"PostgresAdapter",
	"RedisAdapter",
	"Logger",
	"Metrics",
	"ObservabilityOptions",
	"SqliteAdapter",
	"StorageAdapter",
	"StoredFingerprint",
	"DefaultMetrics",
	"calculate_confidence",
	"calculate_confidence_breakdown",
	"calculate_confidence_profile",
	"create_confidence_calculator",
	"create_in_memory_adapter",
	"create_postgres_adapter",
	"create_redis_adapter",
	"create_sqlite_adapter",
	"createInMemoryAdapter",
	"createPostgresAdapter",
	"createRedisAdapter",
	"createSqliteAdapter",
	"canonicalized_stringify",
	"compare_hashes",
	"get_hash",
	"get_tlsh_hash",
	"get_hash_difference",
	"default_logger",
	"default_metrics",
	"clear_registry",
	"get_global_registry",
	"register_comparator",
	"register_plugin",
	"register_weight",
	"set_default_weight",
	"initialize_default_registry",
	"unregister_comparator",
	"unregister_weight",
	"compareHashes",
	"createConfidenceCalculator",
	"calculateConfidence",
	"calculateConfidenceBreakdown",
	"calculateConfidenceProfile",
	"registerComparator",
	"registerPlugin",
	"registerWeight",
	"unregisterComparator",
	"unregisterWeight",
	"setDefaultWeight",
	"clearRegistry",
	"initializeDefaultRegistry",
	"FamilyScore",
]

compareHashes = compare_hashes
createConfidenceCalculator = create_confidence_calculator
calculateConfidence = calculate_confidence
calculateConfidenceBreakdown = calculate_confidence_breakdown
calculateConfidenceProfile = calculate_confidence_profile
registerComparator = register_comparator
registerPlugin = register_plugin
registerWeight = register_weight
unregisterComparator = unregister_comparator
unregisterWeight = unregister_weight
setDefaultWeight = set_default_weight
clearRegistry = clear_registry
initializeDefaultRegistry = initialize_default_registry
createInMemoryAdapter = create_in_memory_adapter
createPostgresAdapter = create_postgres_adapter
createRedisAdapter = create_redis_adapter
createSqliteAdapter = create_sqlite_adapter
