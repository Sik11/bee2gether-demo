import {reactive, toRefs} from 'vue';


let positionTracker = null

// an object containing this user's location
export const userLocation = reactive({

    location : {lng: 0, lat: 0},
    tracking : false


});


// start tracking the user's location
export function startTrackingLocation() {
    if (userLocation.tracking) {
        return;
    }
    positionTracker = navigator.geolocation.watchPosition(
        // success callback
        (position) => {
            userLocation.location = {
                lng: position.coords.longitude,
                lat: position.coords.latitude
            }
            // console.log(userLocation.location);
        },
        // error callback
        (error) => {
            console.log(error);
        },
        // options
        {
            maximumAge: 0
        }   
    );
    userLocation.tracking = true;
}


// get ref to user's location
export function getUserLocation() {
    return userLocation;
}