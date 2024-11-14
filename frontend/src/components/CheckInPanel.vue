<template>
	<div class="flex flex-col bg-white rounded w-full py-6 px-4 border-none">
		<h2 class="text-lg font-bold text-gray-900">Hey, {{ employee?.data?.first_name }} 👋</h2>

		<template v-if="settings.data?.allow_employee_checkin_from_mobile_app">
			<div class="font-medium text-sm text-gray-500 mt-1.5" v-if="lastLog">
				<span>Last {{ lastLogType }} was at {{ formatTimestamp(lastLogTime) }}</span>
				<span class="whitespace-pre"> &middot; </span>
				<router-link :to="{ name: 'EmployeeCheckinListView' }" v-slot="{ navigate }">
					<span @click="navigate" class="underline">View List</span>
				</router-link>
			</div>
			
			<!-- Check In / Check Out Button -->
			<Button
				class="mt-4 mb-1 drop-shadow-sm py-5 text-base"
				id="open-checkin-modal"
				@click="handleEmployeeCheckin"
			>
				<template #prefix>
					<FeatherIcon
						:name="nextAction.action === 'IN' ? 'arrow-right-circle' : 'arrow-left-circle'"
						class="w-4"
					/>
				</template>
				{{ nextAction.label }}
			</Button>
		</template>

		<div v-else class="font-medium text-sm text-gray-500 mt-1.5">
			{{ dayjs().format("ddd, D MMMM, YYYY") }}
		</div>
	</div>

	<!-- Modal for QR Code and Check-in/Check-out Details -->
	<ion-modal
		v-if="settings.data?.allow_employee_checkin_from_mobile_app"
		ref="modal"
		trigger="open-checkin-modal"
		:initial-breakpoint="1"
		:breakpoints="[0, 1]"
	>
		<div class="h-120 w-full flex flex-col items-center justify-center gap-5 p-4 mb-5">
			<div class="flex flex-col gap-1.5 mt-2 mb-2 items-center justify-center">
				<div class="font-bold text-xl">
					{{ currentLogType }}: {{ dayjs(checkinTimestamp).format("hh:mm:ss a") }}
				</div>
				<div class="font-medium text-gray-500 text-sm">
					{{ dayjs().format("D MMM, YYYY") }}
				</div>
				<!-- Display QR Code with formatted value -->
				<QrcodeVue :value="qrCodeValue" :size="150" />
			</div>
			<!-- Display Last Log Details -->
			<div class="font-medium text-sm text-gray-500 mt-4">
				Last {{ lastLogType }} was at {{ formatTimestamp(lastLogTime) }}
			</div>
		</div>
	</ion-modal>
</template>

<script setup>
import { createResource, createListResource, toast, FeatherIcon } from "frappe-ui"
import { computed, inject, ref, onMounted, onBeforeUnmount } from "vue"
import { IonModal } from "@ionic/vue"
import QrcodeVue from "qrcode.vue"
import { formatTimestamp } from "@/utils/formatters"

const DOCTYPE = "Employee Checkin"
const socket = inject("$socket")
const employee = inject("$employee")
const dayjs = inject("$dayjs")
const checkinTimestamp = ref(null)
const currentLogType = ref("")
const lastLogTime = ref(null)

// Fetch HR settings and employee check-ins
const settings = createResource({
	url: "hrms.api.get_hr_settings",
	auto: true,
})

const checkins = createListResource({
	doctype: DOCTYPE,
	fields: ["name", "employee", "employee_name", "log_type", "time", "device_id"],
	filters: {
		employee: employee.data.name,
	},
	orderBy: "time desc",
})
checkins.reload()

// Computed properties for last log details and next action
const lastLog = computed(() => checkins.data?.[0] || {})
const lastLogType = computed(() => (lastLog?.value?.log_type === "IN" ? "check-in" : "check-out"))
const nextAction = computed(() => {
	// Default to Check In if no last log, otherwise toggle
	return lastLog?.value?.log_type === "IN"
		? { action: "OUT", label: "Check Out" }
		: { action: "IN", label: "Check In" }
})

// Function to handle employee check-in/check-out actions
const handleEmployeeCheckin = () => {
	checkinTimestamp.value = dayjs().format("YYYY-MM-DD HH:mm:ss")
	socket.emit("staff_attendance_log", {
		member: employee.data.name,
		time: checkinTimestamp.value,
		log_type: nextAction.value.action,
	})
}

// Socket setup for real-time updates
onMounted(() => {
	socket.emit("doctype_subscribe", DOCTYPE)
	socket.on("list_update", (data) => {
		if (data.doctype == DOCTYPE) {
			checkins.reload()
		}
	})
	socket.on("staff_attendance_log", (data) => {
		// Update log type and time upon receiving real-time data
		currentLogType.value = data.log_type
		lastLogTime.value = data.time
		checkins.reload()
		// Display a toast notification
		toast({
			title: "Check-in Update",
			text: `Checked ${data.log_type} at ${formatTimestamp(data.time)}`,
			icon: "check-circle",
			position: "bottom-center",
			iconClasses: "text-green-500",
		})
	})
})

onBeforeUnmount(() => {
	socket.emit("doctype_unsubscribe", DOCTYPE)
	socket.off("list_update")
	socket.off("staff_attendance_log")
})
</script>
