<template>
	<div class="flex flex-col bg-white rounded-lg shadow w-full py-6 px-4 border-none">
		<!-- Greeting and Reload Button Row -->
		<div class="flex items-center justify-between mb-4">
			<h2 class="text-xl font-semibold text-gray-900">Hey, {{ employee?.data?.first_name }} 👋</h2>
			<!-- Reload Button with Icon -->
			<Button
				class="text-gray-500 border border-gray-300 hover:border-gray-400 hover:text-gray-700 px-2 py-1 rounded"
				@click="fetchLatestLog"
			>
				<FeatherIcon name="refresh-cw" class="w-5 h-5" />
			</Button>
		</div>

		<!-- Last Check-in Info -->
		<template v-if="settings.data?.allow_employee_checkin_from_mobile_app">
			<div class="font-medium text-sm text-gray-500 mb-4" v-if="lastLog">
				<span>Last {{ lastLogType }} was at {{ formatTimestamp(lastLog.time) }}</span>
				<span class="whitespace-pre"> &middot; </span>
				<router-link :to="{ name: 'EmployeeCheckinListView' }" v-slot="{ navigate }">
					<span @click="navigate" class="underline text-blue-600">View List</span>
				</router-link>
			</div>

			<!-- Check-In/Check-Out Button -->
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

		<!-- Display Date if Check-in from Mobile App is Not Allowed -->
		<div v-else class="font-medium text-sm text-gray-500 mt-1.5 text-center">
			{{ dayjs().format("ddd, D MMMM, YYYY") }}
		</div>
	</div>

	<!-- Modal for QR Code -->
	<ion-modal
		v-if="settings.data?.allow_employee_checkin_from_mobile_app"
		ref="modal"
		trigger="open-checkin-modal"
		:initial-breakpoint="1"
		:breakpoints="[0, 1]"
	>
		<div class="h-120 w-full flex flex-col items-center justify-center gap-5 p-4 mb-5">
			<div class="flex flex-col gap-1.5 mt-2 mb-2 items-center justify-center">
				<div class="flex flex-col gap-1.5 mt-2 mb-2 items-center justify-center">
				<div class="font-bold text-xl">
					{{ dayjs(checkinTimestamp).format("hh:mm:ss a") }}
				</div>
				<div class="font-medium text-gray-500 text-sm">
					{{ dayjs().format("D MMM, YYYY") }}
				</div>
			</div>



				<!-- Display QR Code with formatted value -->
				<QrcodeVue :value="qrCodeValue" :size="150" />
			</div>
			<!-- Display Last Log Details -->
		
<div 
    class="font-medium text-sm text-gray-500 mt-4"
    v-if="lastLog?.time"
>
    Last {{ lastLogType }} was at {{ formatTimestamp(lastLog?.time) }}
</div>

		</div>
	</ion-modal>
</template>

<script setup>
import { createResource, createListResource, toast, FeatherIcon } from "frappe-ui"
import { computed, inject, ref, onMounted, onBeforeUnmount } from "vue"
import { IonModal, modalController } from "@ionic/vue"
// Import QrcodeVue from qrcode.vue
import QrcodeVue from "qrcode.vue"
import { formatTimestamp } from "@/utils/formatters"

// Define constants and state variables
const DOCTYPE = "Employee Checkin"
const socket = inject("$socket")
const employee = inject("$employee")
const dayjs = inject("$dayjs")
const checkinTimestamp = ref(null)
const latitude = ref(0)
const longitude = ref(0)
const locationStatus = ref("")

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

// Computed property to format employee name and current timestamp
const qrCodeValue = computed(() => {
	const name = employee?.data?.name || "Unknown"
	const currentTime = dayjs().format("YYYY-MM-DD HH:mm:ss")
	return `${name}&${latitude.value}&${longitude.value}&${currentTime}`
})

// Computed properties for last log details and next action
const lastLog = computed(() => {
	if (checkins.list.loading || !checkins.data) return {}
	return checkins.data[0]
})

const lastLogType = computed(() => {
	return lastLog?.value?.log_type === "IN" ? "check-in" : "check-out"
})

const nextAction = computed(() => {
	return lastLog?.value?.log_type === "IN"
		? { action: "OUT", label: "Check Out " }
		: { action: "IN", label: "Check In " }
})

// Functions to handle geolocation
function handleLocationSuccess(position) {
	latitude.value = position.coords.latitude
	longitude.value = position.coords.longitude

	locationStatus.value = `
		Latitude: ${Number(latitude.value).toFixed(5)}°,
		Longitude: ${Number(longitude.value).toFixed(5)}°
	`
}

function handleLocationError(error) {
	locationStatus.value = "Unable to retrieve your location"
	if (error) locationStatus.value += `: ERROR(${error.code}): ${error.message}`
}

const fetchLocation = () => {
	if (!navigator.geolocation) {
		locationStatus.value = "Geolocation is not supported by your current browser"
	} else {
		locationStatus.value = "Locating..."
		navigator.geolocation.getCurrentPosition(handleLocationSuccess, handleLocationError)
	}
}

const fetchLatestLog = () => {
	checkins.reload().then(() => {
		toast({
			title: "Reloaded",
			text: "Latest check-in log fetched successfully!",
			icon: "refresh-cw",
			position: "bottom-center",
			iconClasses: "text-blue-500",
		});
	});
};

// Function to handle employee check-in/check-out actions
const handleEmployeeCheckin = () => {
	try {
		checkinTimestamp.value = dayjs().format("YYYY-MM-DD HH:mm:ss")
	} catch (error) {
		
	}

	if (settings.data?.allow_geolocation_tracking) {
		fetchLocation()
	}
}

// Function to submit a check-in/check-out log
const submitLog = (logType) => {
	const action = logType === "IN" ? "Check-in" : "Check-out"

	checkins.insert.submit(
		{
			employee: employee.data.name,
			log_type: logType,
			time: checkinTimestamp.value,
			latitude: latitude.value,
			longitude: longitude.value,
		},
		{
			onSuccess() {
				modalController.dismiss()
				toast({
					title: "Success",
					text: `${action} successful!`,
					icon: "check-circle",
					position: "bottom-center",
					iconClasses: "text-green-500",
				})
			},
			onError() {
				toast({
					title: "Error",
					text: `${action} failed!`,
					icon: "alert-circle",
					position: "bottom-center",
					iconClasses: "text-red-500",
				})
			},
		}
	)
}

// Socket setup for real-time updates
onMounted(() => {

	if (socket && socket.connected) {
        console.log("Socket is connected");
    } else {
        console.error("Socket is not connected");
    }	
	socket.emit("doctype_subscribe", DOCTYPE)
	socket.on("list_update", (data) => {
		if (data.doctype == DOCTYPE) {
			checkins.reload()
		}
	})
	socket.on("staff_attendance_log", (data) => {
        console.log("Staff attendance log received:", data);
        checkins.reload();
		modalController.dismiss()
        
        toast({
            title: "Check-in Update",
            text: `Checked ${data.log_type} at ${formatTimestamp(data.time)}`,
            icon: "check-circle",
            position: "bottom-center",
            iconClasses: "text-green-500",
        });
    });
	
})

onBeforeUnmount(() => {
	socket.emit("doctype_unsubscribe", DOCTYPE)
	socket.off("list_update")
	socket.off("staff_attendance_log")
})
</script>









