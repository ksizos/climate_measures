@extends('layouts.app')

@section('title', 'Климатический консультант')

@push('styles')
<link
    rel="stylesheet"
    href="{{ asset('css/climate/index.css') }}">
@endpush


@section('content')

<div class="climate-app">

    <x-climate.sidebar
        :conversations="$conversations" />

    <main class="climate-main">

        <x-climate.header />

        <section class="climate-content">

            <x-climate.welcome />

            <x-climate.messages />

        </section>

        <x-climate.composer />

    </main>

</div>

@endsection


@push('scripts')
<script
    type="module"
    src="{{ asset('js/climate/index.js') }}"></script>
@endpush
